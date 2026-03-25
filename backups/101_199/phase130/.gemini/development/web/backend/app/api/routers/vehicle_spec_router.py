from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from db.database import get_db
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService
from web.backend.app.utils.error_handler import handle_agent_errors
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as VehicleSpecificationService
from web.backend.app.services.model_service import ModelService
from db.models import VehicleSpecification, Model, Product, Asset, Opportunity
from db import models
from web.backend.app.core.templates import templates
import logging

from web.backend.app.core.enums import RecordType

router = APIRouter()
logger = logging.getLogger(__name__)
BRAND_LIST_COLUMNS = ["name", "type", "description"]
BRAND_LIST_BUILTINS = (
    {"id": "brand-all", "label": "All Brands", "source": "all"},
    {"id": "brand-recent", "label": "Recently Viewed", "source": "recent"},
)
MODEL_LIST_COLUMNS = ["name", "brand", "description"]
MODEL_LIST_BUILTINS = (
    {"id": "model-all", "label": "All Models", "source": "all"},
    {"id": "model-recent", "label": "Recently Viewed", "source": "recent"},
)
MODEL_PAGE_SIZE = 50


@router.get("/vehicle_specifications/views")
@handle_agent_errors
async def list_brand_views(db: Session = Depends(get_db)):
    views = LeadListViewService.list_views(db, BRAND_LIST_COLUMNS, object_type="Brand", builtin_views=BRAND_LIST_BUILTINS)
    pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
    return {"views": views, "pinned_view_id": pinned_view_id}


@router.post("/vehicle_specifications/views")
@handle_agent_errors
async def create_brand_view(payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.create_view(db, payload, BRAND_LIST_COLUMNS, object_type="Brand", builtin_views=BRAND_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.put("/vehicle_specifications/views/{view_id}")
@handle_agent_errors
async def update_brand_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.update_view(db, view_id, payload, BRAND_LIST_COLUMNS, object_type="Brand", builtin_views=BRAND_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.delete("/vehicle_specifications/views/{view_id}")
@handle_agent_errors
async def delete_brand_view(view_id: str, db: Session = Depends(get_db)):
    try:
        LeadListViewService.delete_view(db, view_id, object_type="Brand", builtin_views=BRAND_LIST_BUILTINS)
        return JSONResponse(content={"status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.post("/vehicle_specifications/views/{view_id}/pin")
@handle_agent_errors
async def pin_brand_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
    payload = payload or {}
    try:
        pinned_view_id = LeadListViewService.set_pinned_view(db, view_id, BRAND_LIST_COLUMNS, pinned=bool(payload.get("pinned", True)), object_type="Brand", builtin_views=BRAND_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.get("/models/views")
@handle_agent_errors
async def list_model_views(db: Session = Depends(get_db)):
    views = LeadListViewService.list_views(db, MODEL_LIST_COLUMNS, object_type="Model", builtin_views=MODEL_LIST_BUILTINS)
    pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
    return {"views": views, "pinned_view_id": pinned_view_id}


@router.post("/models/views")
@handle_agent_errors
async def create_model_view(payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.create_view(db, payload, MODEL_LIST_COLUMNS, object_type="Model", builtin_views=MODEL_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.put("/models/views/{view_id}")
@handle_agent_errors
async def update_model_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.update_view(db, view_id, payload, MODEL_LIST_COLUMNS, object_type="Model", builtin_views=MODEL_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.delete("/models/views/{view_id}")
@handle_agent_errors
async def delete_model_view(view_id: str, db: Session = Depends(get_db)):
    try:
        LeadListViewService.delete_view(db, view_id, object_type="Model", builtin_views=MODEL_LIST_BUILTINS)
        return JSONResponse(content={"status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.post("/models/views/{view_id}/pin")
@handle_agent_errors
async def pin_model_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
    payload = payload or {}
    try:
        pinned_view_id = LeadListViewService.set_pinned_view(db, view_id, MODEL_LIST_COLUMNS, pinned=bool(payload.get("pinned", True)), object_type="Model", builtin_views=MODEL_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})

@router.get("/vehicle_specifications/new", response_class=HTMLResponse)
@handle_agent_errors
async def new_vehicle_spec_form(request: Request):
    return templates.TemplateResponse(request, "brands/create_edit.html", {
        "request": request,
        "object_type": "Brand",
        "plural_type": "vehicle_specifications",
        "record_type_enum": RecordType,
        "is_new": True
    })

@router.get("/vehicle_specifications/{spec_id}")
@handle_agent_errors
async def vehicle_spec_detail(request: Request, spec_id: str, db: Session = Depends(get_db)):
    logger.info(f"Accessing Vehicle Specification Detail: {spec_id}")
    spec = VehicleSpecificationService.get_vehicle_spec(db, spec_id)
    if not spec: return RedirectResponse(url="/vehicle_specifications")
    details = {
        "Name": spec.name if spec.name else "",
        "Record_Type": spec.record_type if spec.record_type else "",
        "Parent": spec.parent if spec.parent else "",
        "Parent_Hidden_Ref": spec.parent if spec.parent else ""
    }
    related_lists = []
    models_list = db.query(Model).filter(Model.brand == spec_id, Model.deleted_at == None).order_by(Model.name.asc()).all()
    if models_list:
        related_lists.append({
            "title": "Models",
            "icon": "model",
            "columns": ["Name", "Description"],
            "new_url": f"/models/new-modal?brand={spec_id}",
            "view_all_url": f"/models?brand={spec_id}&related=1&back_to=/vehicle_specifications/{spec_id}?tab=related",
            "total_count": len(models_list),
            "items": [{"name": m.name or "", "description": m.description or "", "_href": f"/models/{m.id}"} for m in models_list[:5]],
        })

    products = db.query(Product).filter(Product.brand == spec_id, Product.deleted_at == None).order_by(Product.name.asc()).all()
    if products:
        related_lists.append({
            "title": "Products",
            "icon": "product",
            "columns": ["Name", "Category", "Price"],
            "new_url": f"/products/new-modal?brand={spec_id}",
            "view_all_url": f"/products?brand={spec_id}&related=1&back_to=/vehicle_specifications/{spec_id}?tab=related",
            "total_count": len(products),
            "items": [{"name": p.name or "", "category": p.category or "", "price": f"{p.base_price:,}" if p.base_price else "0", "_href": f"/products/{p.id}"} for p in products[:5]],
        })

    assets = db.query(Asset).filter(Asset.brand == spec_id, Asset.deleted_at == None).order_by(Asset.name.asc()).all()
    if assets:
        related_lists.append({
            "title": "Assets",
            "icon": "asset",
            "columns": ["Name", "Vin", "Status"],
            "new_url": f"/assets/new-modal?brand={spec_id}",
            "view_all_url": f"/assets?brand={spec_id}&related=1&back_to=/vehicle_specifications/{spec_id}?tab=related",
            "total_count": len(assets),
            "items": [{"name": a.name or "", "vin": a.vin or "", "status": a.status or "", "_href": f"/assets/{a.id}"} for a in assets[:5]],
        })

    opportunities = db.query(Opportunity).filter(Opportunity.brand == spec_id, Opportunity.deleted_at == None).order_by(Opportunity.name.asc()).all()
    if opportunities:
        related_lists.append({
            "title": "Opportunities",
            "icon": "opportunity",
            "columns": ["Name", "Stage", "Amount"],
            "new_url": f"/opportunities/new-modal?brand={spec_id}",
            "view_all_url": f"/opportunities?brand={spec_id}&related=1&back_to=/vehicle_specifications/{spec_id}?tab=related",
            "total_count": len(opportunities),
            "items": [{"name": o.name or "", "stage": o.stage or "", "amount": f"{o.amount:,}" if o.amount else "0", "_href": f"/opportunities/{o.id}"} for o in opportunities[:5]],
        })

    return templates.TemplateResponse(request, "brands/detail_view.html", {
        "request": request,
        "object_type": "Brand",
        "plural_type": "vehicle_specifications",
        "record_id": spec_id,
        "record_name": spec.name if spec.name else "",
        "details": details,
        "created_at": spec.created_at,
        "updated_at": spec.updated_at,
        "related_lists": related_lists
    })

@router.get("/vehicle_specifications")
@handle_agent_errors
async def list_specs(request: Request, db: Session = Depends(get_db)):
    related_mode = request.query_params.get("related") == "1" or bool(request.query_params.get("back_to"))
    back_url = request.query_params.get("back_to") or "/vehicle_specifications"
    record_id = request.query_params.get("id")
    if record_id:
        related_mode = True
    specs = db.query(VehicleSpecification).filter(VehicleSpecification.id == record_id).all() if record_id else VehicleSpecificationService.get_vehicle_specs(db)
    items = []
    for s in specs:
        items.append({
            "id": s.id,
            "name": s.name if s.name else "",
            "type": s.record_type if s.record_type else "",
            "description": s.description if s.description else "",
            "edit_url": f"/vehicle_specifications/new?type={s.record_type}&id={s.id}",
            "_href": f"/vehicle_specifications/{s.id}"
        })
    if related_mode:
        return templates.TemplateResponse(request, "related/list_view.html", {
            "request": request,
            "page_title": "Brands",
            "items": items,
            "columns": BRAND_LIST_COLUMNS,
            "back_url": back_url,
            "new_url": "/vehicle_specifications/new?type=Brand",
            "page_icon": "brand",
            "show_actions": True,
        })
    saved_views = LeadListViewService.list_views(db, BRAND_LIST_COLUMNS, object_type="Brand", builtin_views=BRAND_LIST_BUILTINS)
    saved_view_ids = {view["id"] for view in saved_views}
    pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
    requested_view = request.query_params.get("view")
    current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "brand-all")
    return templates.TemplateResponse(request, "brands/list_view.html", {
        "request": request,
        "object_type": "Brand",
        "plural_type": "vehicle_specifications",
        "items": items,
        "columns": BRAND_LIST_COLUMNS,
        "current_view": current_view,
        "list_view_options": [{"value": view["id"], "label": view["label"]} for view in saved_views],
        "saved_views": saved_views,
        "pinned_view_id": pinned_view_id,
        "list_view_storage_key": "d4_recent_brands",
    })

@router.post("/vehicle_specifications")
@handle_agent_errors
async def create_spec(
    name: Optional[str] = Form(None),
    record_type: Optional[str] = Form(None),
    parent: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    spec = VehicleSpecService.create_spec(
        db, name=name, record_type=record_type, parent=parent, description=description
    )
    return RedirectResponse(url=f"/vehicle_specifications/{spec.id}?success=Record+created+successfully", status_code=303)

@router.post("/vehicle_specifications/{spec_id}")
@handle_agent_errors
async def update_spec(
    spec_id: str,
    name: Optional[str] = Form(None),
    record_type: Optional[str] = Form(None),
    parent: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    VehicleSpecService.update_vehicle_spec(
        db, spec_id, name=name, record_type=record_type, parent=parent, description=description
    )
    return RedirectResponse(url=f"/vehicle_specifications/{spec_id}" + "?success=Record+updated+successfully", status_code=303)

@router.post("/vehicle_specifications/{spec_id}/delete")
@handle_agent_errors
async def delete_spec(request: Request, spec_id: str, db: Session = Depends(get_db)):
    VehicleSpecService.delete_vehicle_spec(db, spec_id)
    if "application/json" in request.headers.get("Accept", ""):
        return {"status": "success", "message": "Record deleted successfully"}
    return RedirectResponse(url="/vehicle_specifications?success=Record+deleted+successfully", status_code=303)

@router.post("/vehicle_specifications/{spec_id}/restore")
@handle_agent_errors
async def restore_spec_endpoint(spec_id: str, db: Session = Depends(get_db)):
    VehicleSpecService.restore(db, spec_id)
    return {"status": "success"}

# --- MODELS ---
@router.get("/models/{model_id}")
async def model_detail(request: Request, model_id: str, db: Session = Depends(get_db)):
    try:
        logger.info(f"Accessing Model Detail: {model_id}")
        model = ModelService.get_model(db, model_id)
        if not model: return RedirectResponse(url="/models?error=Model+not+found")

        brand = BrandService.get_vehicle_spec(db, model.brand) if model.brand else None

        details = {
            "Name": model.name if model.name else "",
            "Brand": brand.name if brand else "",
            "Brand_Hidden_Ref": model.brand if model.brand else "",
            "Description": model.description if model.description else ""
        }

        return templates.TemplateResponse(request, "models/detail_view.html", {
            "request": request, "object_type": "Model", "plural_type": "models",
            "record_id": model_id, "record_name": model.name if model.name else "",
            "details": details, "created_at": model.created_at,
            "updated_at": model.updated_at, "related_lists": []
        })
    except Exception as e:
        logger.error(f"Error loading model detail: {e}")
        return RedirectResponse(url=f"/models?error=Error+loading+model+detail:+{str(e).replace(' ', '+')}")

@router.get("/models")
async def list_models(request: Request, db: Session = Depends(get_db)):
    try:
        related_mode = request.query_params.get("related") == "1" or bool(request.query_params.get("back_to"))
        back_url = request.query_params.get("back_to") or "/models"
        filters = [Model.deleted_at == None]
        record_id = request.query_params.get("id")
        if record_id:
            filters.append(Model.id == record_id)
            related_mode = True
        models_data = (
            db.query(Model)
            .filter(*filters)
            .order_by(Model.name.asc())
            .all()
        )
        brand_ids = {m.brand for m in models_data if m.brand}
        brand_map = {}
        if brand_ids:
            brand_map = {brand.id: brand for brand in db.query(VehicleSpecification).filter(VehicleSpecification.id.in_(brand_ids), VehicleSpecification.deleted_at == None).all()}
        items = []
        for m in models_data:
            brand = brand_map.get(m.brand) if m.brand else None
            items.append({
                "id": m.id,
                "name": m.name if m.name else "",
                "brand": brand.name if brand else "",
                "description": m.description if m.description else "",
                "edit_url": f"/models/new-modal?id={m.id}",
                "_href": f"/models/{m.id}"
            })
        if related_mode:
            new_query = []
            brand_filter = request.query_params.get("brand")
            if brand_filter:
                new_query.append(f"brand={brand_filter}")
            new_url = "/models/new-modal"
            if new_query:
                new_url += "?" + "&".join(new_query)
            return templates.TemplateResponse(request, "related/list_view.html", {
                "request": request,
                "page_title": "Models",
                "items": items,
                "columns": MODEL_LIST_COLUMNS,
                "back_url": back_url,
                "new_url": new_url,
                "page_icon": "model",
                "show_actions": True,
            })
        saved_views = LeadListViewService.list_views(db, MODEL_LIST_COLUMNS, object_type="Model", builtin_views=MODEL_LIST_BUILTINS)
        saved_view_ids = {view["id"] for view in saved_views}
        pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
        requested_view = request.query_params.get("view")
        current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "model-all")
        return templates.TemplateResponse(request, "models/list_view.html", {
            "request": request, "object_type": "Model", "plural_type": "models",
            "items": items,
            "columns": MODEL_LIST_COLUMNS,
            "current_view": current_view,
            "list_view_options": [{"value": view["id"], "label": view["label"]} for view in saved_views],
            "saved_views": saved_views,
            "pinned_view_id": pinned_view_id,
            "list_view_storage_key": "d4_recent_models",
        })
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return RedirectResponse(url="/models?error=Error+listing+models")


@router.post("/models")
async def create_model_route(
    name: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        model = ModelService.create_model(db, name=name, brand=brand, description=description)
        return RedirectResponse(url=f"/models/{model.id}?success=Record+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error creating model: {e}")
        return RedirectResponse(url=f"/models?error=Error+creating+model:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/models/{model_id}")
async def update_model_route(
    model_id: str,
    name: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        ModelService.update_model(db, model_id, name=name, brand=brand, description=description)
        return RedirectResponse(url=f"/models/{model_id}?success=Record+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating model: {e}")
        return RedirectResponse(url=f"/models/{model_id}?error=Error+updating+model:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/models/{model_id}/delete")
async def delete_model_route(request: Request, model_id: str, db: Session = Depends(get_db)):
    try:
        ModelService.delete_model(db, model_id)
        if "application/json" in request.headers.get("Accept", ""):
            return {"status": "success", "message": "Record deleted successfully"}
        return RedirectResponse(url="/models?success=Record+deleted+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        return RedirectResponse(url=f"/models?error=Error+deleting+model:+{str(e).replace(' ', '+')}", status_code=303)
