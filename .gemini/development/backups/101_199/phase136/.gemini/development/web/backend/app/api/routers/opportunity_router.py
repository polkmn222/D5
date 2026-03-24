from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from db.database import get_db
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.backend.app.utils.error_handler import handle_agent_errors
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.asset_service import AssetService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from web.backend.app.core.templates import templates
from web.backend.app.core.enums import OpportunityStage, OpportunityStatus
from db import models
from db.models import Model, Opportunity
from datetime import datetime
import logging

from ai_agent.backend.recommendations import AIRecommendationService

router = APIRouter()
logger = logging.getLogger(__name__)
OPPORTUNITY_LIST_COLUMNS = ["name", "amount", "stage", "model", "created"]
OPPORTUNITY_LIST_BUILTINS = (
    {"id": "opp-all", "label": "All Opportunities", "source": "all"},
    {"id": "opp-recent", "label": "Recently Viewed", "source": "recent"},
)


@router.get("/views")
@handle_agent_errors
async def list_opportunity_views(db: Session = Depends(get_db)):
    views = LeadListViewService.list_views(
        db,
        OPPORTUNITY_LIST_COLUMNS,
        object_type="Opportunity",
        builtin_views=OPPORTUNITY_LIST_BUILTINS,
    )
    pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
    return {"views": views, "pinned_view_id": pinned_view_id}


@router.post("/views")
@handle_agent_errors
async def create_opportunity_view(payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.create_view(
            db,
            payload,
            OPPORTUNITY_LIST_COLUMNS,
            object_type="Opportunity",
            builtin_views=OPPORTUNITY_LIST_BUILTINS,
        )
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.put("/views/{view_id}")
@handle_agent_errors
async def update_opportunity_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.update_view(
            db,
            view_id,
            payload,
            OPPORTUNITY_LIST_COLUMNS,
            object_type="Opportunity",
            builtin_views=OPPORTUNITY_LIST_BUILTINS,
        )
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.delete("/views/{view_id}")
@handle_agent_errors
async def delete_opportunity_view(view_id: str, db: Session = Depends(get_db)):
    try:
        LeadListViewService.delete_view(db, view_id, object_type="Opportunity")
        return JSONResponse(content={"status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.post("/views/{view_id}/pin")
@handle_agent_errors
async def pin_opportunity_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
    payload = payload or {}
    try:
        pinned_view_id = LeadListViewService.set_pinned_view(
            db,
            view_id,
            OPPORTUNITY_LIST_COLUMNS,
            pinned=bool(payload.get("pinned", True)),
            object_type="Opportunity",
            builtin_views=OPPORTUNITY_LIST_BUILTINS,
        )
        return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})

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
            "Temperature": AIRecommendationService.normalize_temperature_label(opp.temperature, fallback=""),
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
        stages = [
            OpportunityStage.PROSPECTING.value,
            OpportunityStage.QUALIFICATION.value,
            OpportunityStage.TEST_DRIVE.value,
            OpportunityStage.VALUE_PROPOSITION.value,
            OpportunityStage.PROPOSAL.value,
            OpportunityStage.NEGOTIATION.value,
            OpportunityStage.CLOSED_WON.value,
            OpportunityStage.CLOSED_LOST.value,
        ]
        path = []
        found_active = False
        for s in stages:
            is_active = (s == opp.stage)
            is_completed = not found_active and not is_active
            if is_active: found_active = True
            path.append({"label": s, "active": is_active, "completed": is_completed})

        related_lists = []
        if contact:
            related_lists.append({
                "title": "Contact",
                "columns": ["Name", "Email", "Phone"],
                "icon": "contact",
                "view_all_url": f"/contacts?id={contact.id}&related=1&back_to=/opportunities/{opp_id}?tab=related",
                "total_count": 1,
                "items": [{
                    "name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "",
                    "email": contact.email or "",
                    "phone": contact.phone or "",
                    "_href": f"/contacts/{contact.id}",
                }],
            })

        if product:
            related_lists.append({
                "title": "Product",
                "columns": ["Name", "Category", "Price"],
                "icon": "product",
                "view_all_url": f"/products?id={product.id}&related=1&back_to=/opportunities/{opp_id}?tab=related",
                "total_count": 1,
                "items": [{
                    "name": product.name or "",
                    "category": product.category or "",
                    "price": f"{product.base_price:,}" if product.base_price else "0",
                    "_href": f"/products/{product.id}",
                }],
            })

        if asset:
            related_lists.append({
                "title": "Asset",
                "columns": ["Name", "Vin", "Status"],
                "icon": "asset",
                "view_all_url": f"/assets?id={asset.id}&related=1&back_to=/opportunities/{opp_id}?tab=related",
                "total_count": 1,
                "items": [{
                    "name": asset.name or "",
                    "vin": asset.vin or "",
                    "status": asset.status or "",
                    "_href": f"/assets/{asset.id}",
                }],
            })

        if model:
            related_lists.append({
                "title": "Model",
                "columns": ["Name", "Description"],
                "icon": "model",
                "view_all_url": f"/models?id={model.id}&related=1&back_to=/opportunities/{opp_id}?tab=related",
                "total_count": 1,
                "items": [{
                    "name": model.name or "",
                    "description": model.description or "",
                    "_href": f"/models/{model.id}",
                }],
            })

        if brand:
            related_lists.append({
                "title": "Brand",
                "columns": ["Name", "Type"],
                "icon": "brand",
                "view_all_url": f"/vehicle_specifications?id={brand.id}&related=1&back_to=/opportunities/{opp_id}?tab=related",
                "total_count": 1,
                "items": [{
                    "name": brand.name or "",
                    "type": brand.record_type or "",
                    "_href": f"/vehicle_specifications/{brand.id}",
                }],
            })
    
        return templates.TemplateResponse(request, "opportunities/detail_view.html", {
            "request": request,
            "object_type": "Opportunity",
            "plural_type": "opportunities",
            "record_id": opp_id,
            "record_name": opp.name,
            "details": details,
            "path": path,
            "stage_options": stages,
            "is_followed": opp.is_followed,
            "created_at": opp.created_at,
            "updated_at": opp.updated_at,
            "related_lists": related_lists
        })
    except Exception as e:
        logger.error(f"Opportunity Detail error: {e}")
        return RedirectResponse(url=f"/opportunities?error=Error+loading+opportunity+detail:+{str(e).replace(' ', '+')}")

@router.get("/", response_class=HTMLResponse)
@handle_agent_errors
async def list_opportunities(request: Request, db: Session = Depends(get_db)):
    try:
        related_mode = request.query_params.get("related") == "1" or bool(request.query_params.get("back_to"))
        back_url = request.query_params.get("back_to") or "/opportunities"
        query_filters = {"deleted_at": None}
        has_related_filter = False
        for key in ["contact", "product", "asset", "model", "brand"]:
            value = request.query_params.get(key)
            if value:
                query_filters[key] = value
                has_related_filter = True
        related_mode = related_mode or has_related_filter
        filter = request.query_params.get("filter") # Re-add filter parsing
        if filter == "recommend":
             # Recommend Sales: Test Drive or Closed Won
             opps = OpportunityService.get_ai_recommendations(db)
        else:
             opps = db.query(Opportunity).filter_by(**query_filters).all() if len(query_filters) > 1 else OpportunityService.get_opportunities(db)

        model_ids = {opp.model for opp in opps if opp.model}
        model_map = {}
        if model_ids:
            model_map = {model.id: model for model in db.query(Model).filter(Model.id.in_(model_ids), Model.deleted_at == None).all()}

        items = []
        for o in opps:
            created_str = ""
            if o.created_at:
                if isinstance(o.created_at, datetime):
                    created_str = o.created_at.strftime("%Y-%m-%d")
                else:
                    created_str = str(o.created_at)[:10]

            model = model_map.get(o.model) if o.model else None
            items.append({
                "id": o.id,
                "name": o.name,
                "amount": o.amount if o.amount else 0,
                "stage": o.stage,
                "model": model.name if model else "",
                "created": created_str,
                "edit_url": f"/opportunities/new-modal?id={o.id}",
                "_href": f"/opportunities/{o.id}",
            })
        if related_mode:
            new_query = []
            for key in ["contact", "product", "asset", "model", "brand"]:
                value = request.query_params.get(key)
                if value:
                    new_query.append(f"{key}={value}")
            new_url = "/opportunities/new-modal"
            if new_query:
                new_url += "?" + "&".join(new_query)
            return templates.TemplateResponse(request, "related/list_view.html", {
                "request": request,
                "page_title": "Opportunities",
                "items": items,
                "columns": OPPORTUNITY_LIST_COLUMNS,
                "back_url": back_url,
                "new_url": new_url,
                "page_icon": "opportunity",
                "show_actions": True,
            })
        saved_views = LeadListViewService.list_views(
            db,
            OPPORTUNITY_LIST_COLUMNS,
            object_type="Opportunity",
            builtin_views=OPPORTUNITY_LIST_BUILTINS,
        )
        saved_view_ids = {view["id"] for view in saved_views}
        pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
        requested_view = request.query_params.get("view")
        current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "opp-all")
        return templates.TemplateResponse(request, "opportunities/list_view.html", {
            "request": request, 
            "object_type": "Opportunity", 
            "plural_type": "opportunities",
            "items": items, 
            "columns": OPPORTUNITY_LIST_COLUMNS,
            "current_view": current_view,
            "list_view_options": [
                {"value": view["id"], "label": view["label"]}
                for view in saved_views
            ],
            "saved_views": saved_views,
            "pinned_view_id": pinned_view_id,
            "list_view_storage_key": "d4_recent_opportunities",
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
    record = OpportunityService.get_opportunity(db, opp_id)
    if not record:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Record not found."})

    clean_updates = {}
    for k, v in updates.items():
        key = k.lower().replace(" ", "_")
        if key == "opportunity_name":
            clean_updates["name"] = v
        elif key == "contact_hidden_ref":
            clean_updates["contact"] = v
        elif key == "brand_hidden_ref":
            clean_updates["brand"] = v
        elif key == "model_hidden_ref":
            clean_updates["model"] = v
        elif key == "product_hidden_ref":
            clean_updates["product"] = v
        elif key == "asset_hidden_ref":
            clean_updates["asset"] = v
        elif key in {"amount", "probability"}:
            cleaned = str(v).replace(",", "").replace("₩", "").strip()
            clean_updates[key] = int(cleaned) if cleaned else 0
        elif key == "close_date":
            if v:
                clean_updates[key] = datetime.fromisoformat(str(v))
        elif hasattr(record, key):
            clean_updates[key] = v

    if not clean_updates:
        return JSONResponse(status_code=400, content={"status": "error", "message": "No editable fields were provided."})
    
    updated = OpportunityService.update_opportunity(db, opp_id, **clean_updates)
    if not updated:
        return JSONResponse(status_code=404, content={"status": "error", "message": "Record not found."})
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


@router.post("/{opp_id}/toggle-follow")
@handle_agent_errors
async def toggle_opportunity_follow_endpoint(opp_id: str, enabled: bool = Form(...), db: Session = Depends(get_db)):
    OpportunityService.toggle_follow(db, opp_id, enabled)
    return {"status": "success", "followed": enabled}

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
