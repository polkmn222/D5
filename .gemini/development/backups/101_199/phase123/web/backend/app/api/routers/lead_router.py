from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from db.models import Lead, Model

from db.database import get_db
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.backend.app.utils.error_handler import handle_agent_errors
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from web.backend.app.core.templates import templates
import logging

from web.backend.app.core.enums import LeadStatus, RecordType

router = APIRouter()
logger = logging.getLogger(__name__)
LEAD_LIST_COLUMNS = ["name", "email", "phone", "model", "status", "created"]


@router.get("/views")
@handle_agent_errors
async def list_lead_views(db: Session = Depends(get_db)):
    views = LeadListViewService.list_views(db, LEAD_LIST_COLUMNS)
    pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
    return {"views": views, "pinned_view_id": pinned_view_id}


@router.post("/views")
@handle_agent_errors
async def create_lead_view(payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.create_view(db, payload, LEAD_LIST_COLUMNS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.put("/views/{view_id}")
@handle_agent_errors
async def update_lead_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.update_view(db, view_id, payload, LEAD_LIST_COLUMNS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.delete("/views/{view_id}")
@handle_agent_errors
async def delete_lead_view(view_id: str, db: Session = Depends(get_db)):
    try:
        LeadListViewService.delete_view(db, view_id)
        return JSONResponse(content={"status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.post("/views/{view_id}/pin")
@handle_agent_errors
async def pin_lead_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
    payload = payload or {}
    try:
        pinned_view_id = LeadListViewService.set_pinned_view(
            db,
            view_id,
            LEAD_LIST_COLUMNS,
            pinned=bool(payload.get("pinned", True)),
        )
        return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})

@router.get("/{lead_id}", response_class=HTMLResponse)
@handle_agent_errors
async def lead_detail(request: Request, lead_id: str, db: Session = Depends(get_db)):
    logger.info(f"Accessing Lead Detail: {lead_id}")
    lead = LeadService.get_lead(db, lead_id)
    if not lead:
        return RedirectResponse(url="/leads?error=Lead+not+found")
    
    brand = BrandService.get_vehicle_spec(db, lead.brand) if lead.brand else None
    model = ModelService.get_model(db, lead.model) if lead.model else None
    prod = ProductService.get_product(db, lead.product) if lead.product else None
    
    details = {
        "Name": f"{lead.first_name if lead.first_name else ''} {lead.last_name if lead.last_name else ''}".strip() or "",
        "Status": lead.status.value if hasattr(lead.status, "value") else (lead.status if lead.status else ""),
        "Brand": brand.name if brand else "",
        "Brand_Hidden_Ref": lead.brand if lead.brand else "",
        "Model": model.name if model else "",
        "Model_Hidden_Ref": lead.model if lead.model else "",
        "Product": prod.name if prod else "",
        "Product_Hidden_Ref": lead.product if lead.product else "",
        "Email": lead.email if lead.email else "",
        "Phone": lead.phone if lead.phone else "",
        "Is Followed": "Yes" if lead.is_followed else "No",
        "Created Date": lead.created_at.strftime("%Y-%m-%d %H:%M") if lead.created_at else ""
    }
    
    # Path/Progress bar
    stages = [LeadStatus.NEW, LeadStatus.FOLLOW_UP, LeadStatus.QUALIFIED, LeadStatus.LOST]
    path = []
    found_active = False
    for s in stages:
        is_active = (s == lead.status or s.value == lead.status)
        is_completed = not found_active and not is_active
        if is_active: found_active = True
        path.append({"label": s.value, "active": is_active, "completed": is_completed})

    return templates.TemplateResponse(request, "leads/detail_view.html", {
        "request": request,
        "object_type": "Lead",
        "plural_type": "leads",
        "record_id": lead_id,
        "record_name": f"{lead.first_name} {lead.last_name}",
        "details": details,
        "path": path,
        "is_followed": lead.is_followed,
        "created_at": lead.created_at,
        "updated_at": lead.updated_at,
        "is_converted": lead.is_converted,
        "related_lists": []
    })

@router.get("/", response_class=HTMLResponse)
@handle_agent_errors
async def list_leads(request: Request, db: Session = Depends(get_db)):
    related_mode = request.query_params.get("related") == "1" or bool(request.query_params.get("back_to"))
    back_url = request.query_params.get("back_to") or "/leads"
    items = []
    filters = {"deleted_at": None, "is_converted": False}
    record_id = request.query_params.get("id")
    if record_id:
        filters["id"] = record_id
        related_mode = True
    for key in ["product", "model", "brand"]:
        value = request.query_params.get(key)
        if value:
            filters[key] = value
            related_mode = True
    leads = db.query(Lead).filter_by(**filters).all() if len(filters) > 2 else LeadService.get_leads(db, converted=False)
    model_ids = {lead.model for lead in leads if lead.model}
    model_map = {}
    if model_ids:
        model_map = {model.id: model for model in db.query(Model).filter(Model.id.in_(model_ids), Model.deleted_at == None).all()}
    for lead in leads:
        model = model_map.get(lead.model) if lead.model else None
        items.append({
            "id": lead.id,
            "name": f"{lead.first_name if lead.first_name else ''} {lead.last_name if lead.last_name else ''}".strip() or "",
            "email": lead.email if lead.email else "",
            "phone": lead.phone if lead.phone else "",
            "model": model.name if model else "",
            "status": lead.status.value if hasattr(lead.status, "value") else (lead.status if lead.status else ""),
            "created": lead.created_at.strftime("%Y-%m-%d") if lead.created_at else "",
            "edit_url": f"/leads/new-modal?id={lead.id}",
            "_href": f"/leads/{lead.id}"
        })

    if related_mode:
        return templates.TemplateResponse(request, "related/list_view.html", {
            "request": request,
            "page_title": "Leads",
            "items": items,
            "columns": LEAD_LIST_COLUMNS,
            "back_url": back_url,
            "new_url": None,
            "show_actions": True,
        })

    saved_views = LeadListViewService.list_views(db, LEAD_LIST_COLUMNS)
    saved_view_ids = {view["id"] for view in saved_views}
    pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
    requested_view = request.query_params.get("view")
    current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "all")

    return templates.TemplateResponse(request, "leads/list_view.html", {
        "request": request,
        "object_type": "Lead",
        "plural_type": "leads",
        "items": items,
        "columns": LEAD_LIST_COLUMNS,
        "current_view": current_view,
        "list_view_options": [
            {"value": view["id"], "label": view["label"]}
            for view in saved_views
        ],
        "saved_views": saved_views,
        "pinned_view_id": pinned_view_id,
        "list_view_storage_key": "d4_recent_leads",
    })

@router.get("/new", response_class=HTMLResponse)
@handle_agent_errors
async def new_lead_form(request: Request):
    return templates.TemplateResponse(request, "leads/create_edit_modal.html", {
        "request": request,
        "object_type": "Lead",
        "is_new": True
    })

@router.post("/")
@handle_agent_errors
async def create_lead(
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    product: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    lead = LeadService.create_lead(
        db, first_name=first_name, last_name=last_name, gender=gender,
        email=email, phone=phone,
        brand=brand, model=model, 
        product=product, description=description, status=LeadStatus.NEW
    )
    return RedirectResponse(url=f"/leads/{lead.id}?success=Record+created+successfully", status_code=303)

@router.post("/{lead_id}")
@handle_agent_errors
async def update_lead_direct(
    lead_id: str,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    product: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    return await update_lead(lead_id, first_name, last_name, gender, email, phone, status, brand, model, product, description, db)

@router.post("/{lead_id}/update")
@handle_agent_errors
async def update_lead(
    lead_id: str,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    product: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    LeadService.update_lead(
        db, lead_id, first_name=first_name, last_name=last_name, gender=gender,
        email=email, phone=phone, status=status,
        brand=brand, model=model, 
        product=product, description=description
    )
    return RedirectResponse(url=f"/leads/{lead_id}?success=Record+updated+successfully", status_code=303)

@router.post("/{lead_id}/batch-save")
@handle_agent_errors
async def batch_save_lead(lead_id: str, updates: dict, db: Session = Depends(get_db)):
    """Handles JSON batch updates from inline editing."""
    clean_updates = {}
    for k, v in updates.items():
        key = k.lower().replace(" ", "_")
        clean_updates[key] = v
    
    LeadService.update_lead(db, lead_id, **clean_updates)
    return {"status": "success"}

@router.post("/{lead_id}/delete")
@handle_agent_errors
async def delete_lead(request: Request, lead_id: str, db: Session = Depends(get_db)):
    LeadService.delete_lead(db, lead_id)
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/leads?success=Record+deleted+successfully", status_code=303)


@router.get("/{lead_id}/convert", response_class=HTMLResponse)
@handle_agent_errors
async def convert_lead_modal(request: Request, lead_id: str, db: Session = Depends(get_db)):
    lead = LeadService.get_lead(db, lead_id)
    if not lead:
        return RedirectResponse(url="/leads?error=Lead+not+found")
    return templates.TemplateResponse(request, "leads/lead_convert_modal.html", {
        "request": request,
        "lead": lead
    })


@router.post("/{lead_id}/convert")
async def convert_lead(
    request: Request,
    lead_id: str, 
    contact_name: str = Form(None),
    opportunity_name: str = Form(None),
    dont_create_opp: bool = Form(False),
    converted_status: str = Form("Closed - Converted"),
    db: Session = Depends(get_db)
):
    try:
        result = LeadService.convert_lead_advanced(
            db, lead_id, contact_name, 
            opportunity_name, dont_create_opp, converted_status
        )
        if result and "contact" in result:
            return templates.TemplateResponse(request, "leads/lead_convert_success.html", {
                "request": request,
                "contact": result["contact"],
                "opportunity": result["opportunity"]
            })
        return RedirectResponse(url=f"/leads/{lead_id}?error=Failed+to+convert+lead", status_code=303)
    except Exception as e:
        logger.error(f"Error converting lead: {str(e)}")
        return RedirectResponse(url=f"/leads/{lead_id}?error=Error+converting+lead:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{lead_id}/stage")
async def update_lead_stage_endpoint(lead_id: str, stage: str = Form(...), db: Session = Depends(get_db)):
    try:
        LeadService.update_stage(db, lead_id, stage)
        return {"status": "success", "new_stage": stage}
    except Exception as e:
        logger.error(f"Error updating lead stage: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/{lead_id}/toggle-follow")
async def toggle_lead_follow_endpoint(lead_id: str, enabled: bool = Form(...), db: Session = Depends(get_db)):
    LeadService.toggle_follow(db, lead_id, enabled)
    return {"status": "success", "followed": enabled}

@router.post("/{lead_id}/restore")
async def restore_lead_endpoint(lead_id: str, db: Session = Depends(get_db)):
    LeadService.restore_lead(db, lead_id)
    return {"status": "success"}
