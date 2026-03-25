from typing import Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from db.database import get_db
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.utils.error_handler import handle_agent_errors
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.asset_service import AssetService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from web.backend.app.core.templates import templates
from web.backend.app.core.enums import OpportunityStage, OpportunityStatus
from db import models
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{opp_id}", response_class=HTMLResponse)
@handle_agent_errors
async def opportunity_detail(request: Request, opp_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Accessing Opportunity Detail: {opp_id}")
        # track visit for history
        OpportunityService.update_last_viewed(db, opp_id)
        opp = OpportunityService.get_opportunity(db, opp_id)
        if not opp:
            return RedirectResponse(url="/opportunities?error=Opportunity+not+found")
        
        contact = ContactService.get_contact(db, opp.contact) if opp.contact else None
        product = ProductService.get_product(db, opp.product) if opp.product else None
        asset = AssetService.get_asset(db, opp.asset) if opp.asset else None
        
        brand = BrandService.get_vehicle_spec(db, opp.brand) if opp.brand else None
        model = ModelService.get_model(db, opp.model) if opp.model else None

        details = {
            "Opportunity Name": opp.name,
            "Stage": opp.stage,
            "Amount": opp.amount if opp.amount else 0,
            "Temperature": opp.temperature,
            "Close Date": opp.close_date,
            "Contact": f"{contact.first_name} {contact.last_name}" if contact else (contact.name if contact else None),
            "Contact_Hidden_Ref": opp.contact,
            "Brand": brand.name if brand else None,
            "Brand_Hidden_Ref": opp.brand,
            "Model": model.name if model else None,
            "Model_Hidden_Ref": opp.model,
            "Product": product.name if product else None,
            "Product_Hidden_Ref": opp.product,
            "Asset": asset.name if asset else None,
            "Asset_Hidden_Ref": opp.asset
        }
        
        # Path/Progress bar
        stages = [OpportunityStage.PROSPECTING.value, OpportunityStage.QUALIFICATION.value, OpportunityStage.NEEDS_ANALYSIS.value, OpportunityStage.VALUE_PROPOSITION.value, OpportunityStage.CLOSED_WON.value, OpportunityStage.CLOSED_LOST.value]
        path = []
        found_active = False
        for s in stages:
            is_active = (s == opp.stage)
            is_completed = not found_active and not is_active
            if is_active: found_active = True
            path.append({"label": s, "active": is_active, "completed": is_completed})
    
        return templates.TemplateResponse(request, "opportunities/detail_view.html", {
            "request": request,
            "object_type": "Opportunity",
            "plural_type": "opportunities",
            "record_id": opp_id,
            "record_name": opp.name,
            "details": details,
            "path": path,
            "is_followed": opp.is_followed,
            "created_at": opp.created_at,
            "updated_at": opp.updated_at,
            "related_lists": []
        })
    except Exception as e:
        logger.error(f"Opportunity Detail error: {e}")
        return RedirectResponse(url=f"/opportunities?error=Error+loading+opportunity+detail:+{str(e).replace(' ', '+')}")

@router.get("/", response_class=HTMLResponse)
@handle_agent_errors
async def list_opportunities(request: Request, db: Session = Depends(get_db)):
    try:
        filter = request.query_params.get("filter") # Re-add filter parsing
        if filter == "recommend":
             # Recommend Sales: Test Drive or Closed Won
             opps = OpportunityService.get_ai_recommendations(db)
        else:
             opps = OpportunityService.get_opportunities(db)
             
        items = []
        for o in opps:
            created_str = ""
            if o.created_at:
                if isinstance(o.created_at, datetime):
                    created_str = o.created_at.strftime("%Y-%m-%d")
                else:
                    created_str = str(o.created_at)[:10]

            model = ModelService.get_model(db, o.model) if o.model else None
            items.append({
                "id": o.id,
                "name": o.name,
                "amount": o.amount if o.amount else 0,
                "stage": o.stage,
                "model": model.name if model else "",
                "created": created_str,
                "edit_url": f"/opportunities/new-modal?id={o.id}"
            })
        columns = ["name", "amount", "stage", "model", "created"]
        return templates.TemplateResponse(request, "opportunities/list_view.html", {
            "request": request, 
            "object_type": "Opportunity", 
            "plural_type": "opportunities",
            "items": items, 
            "columns": columns
        })
    except Exception as e:
        logger.error(f"List opportunities error: {e}")
        return RedirectResponse(url="/?error=Error+loading+opportunities")

@router.post("/{opp_id}")
@handle_agent_errors
async def update_opportunity(
    opp_id: str,
    contact: Optional[str] = Form(None),
    asset: Optional[str] = Form(None),
    product: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    amount: Optional[int] = Form(None),
    stage: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    probability: Optional[int] = Form(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        OpportunityService.update_opportunity(
            db, opp_id, contact=contact, name=name, amount=amount, 
            stage=stage, status=status, probability=probability,
            brand=brand, model=model,
            asset=asset, product=product
        )
        return RedirectResponse(url=f"/opportunities/{opp_id}?success=Record+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Update Opportunity error: {e}")
        return RedirectResponse(url=f"/opportunities/{opp_id}?error=Error+updating+opportunity:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{opp_id}/batch-save")
@handle_agent_errors
async def batch_save_opportunity(opp_id: str, updates: dict, db: Session = Depends(get_db)):
    """Handles JSON batch updates from inline editing."""
    clean_updates = {}
    for k, v in updates.items():
        key = k.lower().replace(" ", "_")
        clean_updates[key] = v
    
    OpportunityService.update_opportunity(db, opp_id, **clean_updates)
    return {"status": "success"}

@router.post("/{opp_id}/delete")
@handle_agent_errors
async def delete_opportunity(request: Request, opp_id: str, db: Session = Depends(get_db)):
    try:
        OpportunityService.delete_opportunity(db, opp_id)
        if "application/json" in request.headers.get("Accept", ""):
            return {"status": "success", "message": "Record deleted successfully"}
        return RedirectResponse(url="/opportunities?success=Record+deleted+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Delete Opportunity error: {e}")
        return RedirectResponse(url=f"/opportunities?error=Error+deleting+opportunity:+{str(e).replace(' ', '+')}", status_code=303)


@router.post("/{opp_id}/stage")
async def update_opportunity_stage_endpoint(opp_id: str, stage: str = Form(...), db: Session = Depends(get_db)):
    try:
        OpportunityService.update_stage(db, opp_id, stage)
        return {"status": "success", "new_stage": stage}
    except Exception as e:
        logger.error(f"Update Opportunity Stage error: {e}")
        return RedirectResponse(url=f"/opportunities/{opp_id}?error=Error+updating+stage:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{opp_id}/restore")
async def restore_opportunity_endpoint(opp_id: str, db: Session = Depends(get_db)):
    try:
        OpportunityService.restore_opportunity(db, opp_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Restore Opportunity error: {e}")
        return RedirectResponse(url=f"/opportunities?error=Error+restoring+opportunity:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/")
async def create_opportunity(
    contact: Optional[str] = Form(None),
    asset: Optional[str] = Form(None),
    product: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    amount: Optional[int] = Form(None),
    stage: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    probability: Optional[int] = Form(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        opp = OpportunityService.create_opportunity(
            db, contact=contact, name=name, amount=amount, 
            stage=stage, status=status, probability=probability,
            brand=brand, model=model,
            asset=asset, product=product
        )
        return RedirectResponse(url=f"/opportunities/{opp.id}?success=Record+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Create Opportunity error: {e}")
        return RedirectResponse(url=f"/opportunities?error=Error+creating+opportunity:+{str(e).replace(' ', '+')}", status_code=303)
