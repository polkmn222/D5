from typing import Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from db.database import get_db
from backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from backend.app.services.vehicle_spec_service import VehicleSpecService
from backend.app.utils.error_handler import handle_agent_errors
from backend.app.services.vehicle_spec_service import VehicleSpecService as VehicleSpecificationService
from backend.app.services.model_service import ModelService
from db.models import VehicleSpecification
from db import models
from backend.app.core.templates import templates
import logging

from backend.app.core.enums import RecordType

router = APIRouter()
logger = logging.getLogger(__name__)

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
    # Related Models
    from db.models import Model as ModelModel
    models_list = db.query(ModelModel).filter(ModelModel.brand == spec_id).all()
    related_lists = []
    if models_list:
        related_lists.append({
            "title": "Models",
            "columns": ["name", "description"],
            "items": [{"name": m.name, "description": m.description if m.description else ""} for m in models_list]
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
    specs = VehicleSpecificationService.get_vehicle_specs(db)
    items = []
    for s in specs:
        items.append({
            "id": s.id,
            "name": s.name if s.name else "",
            "type": s.record_type if s.record_type else "",
            "description": s.description if s.description else "",
            "edit_url": f"/vehicle_specifications/new?type={s.record_type}&id={s.id}"
        })
    columns = ["name", "type", "description"]
    return templates.TemplateResponse(request, "brands/list_view.html", {
        "request": request,
        "object_type": "Brand",
        "plural_type": "vehicle_specifications",
        "items": items,
        "columns": columns
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
        models_data = ModelService.get_models(db)
        items = []
        for m in models_data:
            brand = BrandService.get_vehicle_spec(db, m.brand) if m.brand else None
            items.append({
                "id": m.id,
                "name": m.name if m.name else "",
                "brand": brand.name if brand else "",
                "description": m.description if m.description else "",
                "edit_url": f"/models/new-modal?id={m.id}"
            })
        columns = ["name", "brand", "description"]
        return templates.TemplateResponse(request, "list_view.html", {
            "request": request, "object_type": "Model", "plural_type": "models",
            "items": items, "columns": columns
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
