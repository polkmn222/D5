from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from db.database import get_db
from web.backend.app.utils.error_handler import handle_agent_errors
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.asset_service import AssetService

from web.backend.app.services.model_service import ModelService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as VehicleSpecificationService
from web.backend.app.services.import_service import ImportService
from web.message.backend.services.message_service import MessageService
from web.message.backend.services.message_template_service import MessageTemplateService
from db import models
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

LOOKUP_FIELD_MAP = {
    "contact_hidden_ref": "contact",
    "opportunity_hidden_ref": "opportunity",
    "brand_hidden_ref": "brand",
    "model_hidden_ref": "model",
    "product_hidden_ref": "product",
    "asset_hidden_ref": "asset",
    "message_hidden_ref": "message",
    "template_hidden_ref": "template",
}


def _normalize_lookup_value(value):
    if isinstance(value, str):
        value = value.strip()
    return None if value == "" else value


def _active_lookup_records(db: Session, lookup_type: str, query: str = "", limit: int = 5):
    q_filter = f"%{query}%"
    if lookup_type == "Contact":
        return db.query(models.Contact).filter(
            models.Contact.deleted_at == None,
            or_(
                (models.Contact.first_name + " " + models.Contact.last_name).ilike(q_filter),
                models.Contact.name.ilike(q_filter)
            )
        ).limit(limit).all()
    if lookup_type == "Product":
        return db.query(models.Product).filter(models.Product.deleted_at == None, models.Product.name.ilike(q_filter)).limit(limit).all()
    if lookup_type == "Asset":
        return db.query(models.Asset).filter(models.Asset.deleted_at == None, models.Asset.name.ilike(q_filter)).limit(limit).all()
    if lookup_type in {"VehicleSpecification", "Brand"}:
        return db.query(models.VehicleSpecification).filter(
            models.VehicleSpecification.deleted_at == None,
            models.VehicleSpecification.record_type == "Brand",
            models.VehicleSpecification.name.ilike(q_filter)
        ).limit(limit).all()
    if lookup_type == "Model":
        return db.query(models.Model).filter(models.Model.deleted_at == None, models.Model.name.ilike(q_filter)).limit(limit).all()
    if lookup_type in {"Message", "MessageSend"}:
        return db.query(models.MessageSend).filter(models.MessageSend.deleted_at == None, models.MessageSend.content.ilike(q_filter)).limit(limit).all()
    if lookup_type in {"MessageTemplate", "Template"}:
        return db.query(models.MessageTemplate).filter(models.MessageTemplate.deleted_at == None, models.MessageTemplate.name.ilike(q_filter)).limit(limit).all()
    return []


def _serialize_lookup_result(lookup_type: str, item):
    if lookup_type == "Contact":
        display_name = item.name if item.name else f"{item.first_name} {item.last_name}".strip()
        return {"id": item.id, "name": display_name, "type": "Contact"}
    if lookup_type == "Product":
        return {"id": item.id, "name": item.name, "type": "Product"}
    if lookup_type == "Asset":
        return {"id": item.id, "name": item.name, "type": "Asset", "price": item.price}
    if lookup_type in {"VehicleSpecification", "Brand"}:
        return {"id": item.id, "name": item.name, "type": "Brand"}
    if lookup_type == "Model":
        return {"id": item.id, "name": item.name, "type": "Model"}
    if lookup_type in {"Message", "MessageSend"}:
        display = item.content[:50] + "..." if item.content and len(item.content) > 50 else (item.content or "")
        return {"id": item.id, "name": display, "type": "MessageSend"}
    if lookup_type in {"MessageTemplate", "Template"}:
        return {"id": item.id, "name": item.name, "type": "MessageTemplate"}
    return {"id": item.id, "name": getattr(item, "name", item.id), "type": lookup_type}


def _build_update_data(object_type: str, data: dict) -> dict:
    update_data = {}
    force_null_fields = set()

    for field, value in data.items():
        field_norm = field.lower().replace(" ", "_")

        if field_norm in LOOKUP_FIELD_MAP:
            target_field = LOOKUP_FIELD_MAP[field_norm]
            normalized_value = _normalize_lookup_value(value)
            update_data[target_field] = normalized_value
            if normalized_value is None:
                force_null_fields.add(target_field)
        elif field_norm == "opportunity_name":
            update_data["name"] = value
        elif field_norm == "name" and object_type in ["leads", "contacts"]:
            parts = str(value).split(" ", 1)
            update_data["first_name"] = parts[0]
            update_data["last_name"] = parts[1] if len(parts) > 1 else ""
        elif field_norm == "type" and object_type == "message_templates":
            update_data["record_type"] = value
        elif field_norm == "description" and object_type == "message_templates":
            update_data["content"] = value
        else:
            normalized_value = value
            if field_norm in ["amount", "price", "budget", "base_price", "probability"]:
                normalized_value = str(value).replace(",", "").replace("₩", "").strip()
                normalized_value = "0" if not normalized_value else normalized_value
            update_data[field_norm] = normalized_value

    if force_null_fields:
        update_data["_force_null_fields"] = sorted(force_null_fields)
    return update_data

@router.post("/{object_type}/{record_id}/inline-save")
@handle_agent_errors
async def inline_save(object_type: str, record_id: str, field: str = Form(...), value: str = Form(...), db: Session = Depends(get_db)):
        field_name = field.lower().replace(" ", "_")
        
        object_type_map = {
            "leads": (LeadService, LeadService.get_lead),
            "opportunities": (OpportunityService, OpportunityService.get_opportunity),
            "contacts": (ContactService, ContactService.get_contact),
            "assets": (AssetService, AssetService.get_asset),
            "products": (ProductService, ProductService.get_product),
            "vehicle_specifications": (VehicleSpecificationService, VehicleSpecificationService.get_vehicle_spec),

            "models": (ModelService, ModelService.get_model),
            "messages": (MessageService, MessageService.get_message),
            "message_templates": (MessageTemplateService, MessageTemplateService.get_template)
        }

        record_tuple = object_type_map.get(object_type)

        if not record_tuple:
            logger.error(f"Object type {object_type} not supported for inline save")
            return {"status": "error", "message": "Object type not supported"}
            
        service, get_method = record_tuple
        record = get_method(db, record_id)
        
        if record:
            update_data = _build_update_data(object_type, {field: value})

            service_update_func = None
            if object_type == "vehicle_specifications":
                service_update_func = service.update_vehicle_spec
            elif object_type == "opportunities":
                service_update_func = service.update_opportunity
            elif object_type == "leads":
                service_update_func = service.update_lead
            elif object_type == "contacts":
                service_update_func = service.update_contact
            elif object_type == "products":
                service_update_func = service.update_product
            elif object_type == "models":
                service_update_func = service.update_model
            elif object_type == "messages":
                service_update_func = service.update_message
            elif object_type == "message_templates":
                service_update_func = service.update_template
            else:
                if object_type.endswith('ies'):
                    singular_type = object_type[:-3] + 'y'
                elif object_type.endswith('s'):
                    singular_type = object_type[:-1]
                else:
                    singular_type = object_type
                service_update_func = getattr(service, f"update_{singular_type}", None)

            if service_update_func and update_data:
                service_update_func(db, record_id, **update_data)
                logger.info(f"Field {field_name} updated for {object_type} {record_id}")
                return {"status": "success", "field": field_name, "value": value}
            else:
                logger.error(f"Update function not found for object type {object_type}")
                return {"status": "error", "message": "Update function not found"}
        
        return {"status": "error", "message": "Record not found"}


@router.post("/{object_type}/{record_id}/batch-save")
@handle_agent_errors
async def batch_save(object_type: str, record_id: str, request: Request, db: Session = Depends(get_db)):
    """Accepts a JSON object of field-value pairs and updates the record."""
    try:
        data = await request.json()
    except Exception as e:
        logger.error(f"Error parsing JSON for batch save: {e}")
        return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid JSON"})

    object_type_map = {
        "leads": (LeadService, LeadService.get_lead),
        "opportunities": (OpportunityService, OpportunityService.get_opportunity),
        "contacts": (ContactService, ContactService.get_contact),
        "assets": (AssetService, AssetService.get_asset),
        "products": (ProductService, ProductService.get_product),
        "vehicle_specifications": (VehicleSpecificationService, VehicleSpecificationService.get_vehicle_spec),

        "models": (ModelService, ModelService.get_model),
        "messages": (MessageService, MessageService.get_message),
        "message_templates": (MessageTemplateService, MessageTemplateService.get_template)
    }

    record_tuple = object_type_map.get(object_type)
    if not record_tuple:
        return {"status": "error", "message": "Object type not supported"}
        
    service, get_method = record_tuple
    record = get_method(db, record_id)
    if not record:
        return {"status": "error", "message": "Record not found"}

    update_data = _build_update_data(object_type, data)

    # Identify update function
    if object_type == "vehicle_specifications": service_update_func = service.update_vehicle_spec
    elif object_type == "opportunities": service_update_func = service.update_opportunity
    elif object_type == "leads": service_update_func = service.update_lead
    elif object_type == "contacts": service_update_func = service.update_contact
    elif object_type == "products": service_update_func = service.update_product
    elif object_type == "models": service_update_func = service.update_model
    elif object_type == "messages": service_update_func = service.update_message
    elif object_type == "message_templates": service_update_func = service.update_template
    else:
        singular = object_type.rstrip('s')
        if object_type.endswith('ies'): singular = object_type[:-3] + 'y'
        service_update_func = getattr(service, f"update_{singular}", None)

    force_null_fields = set(update_data.get("_force_null_fields", []))
    valid_update_data = {key: value for key, value in update_data.items() if key == "_force_null_fields" or hasattr(record, key)}
    if not valid_update_data:
        return JSONResponse(status_code=400, content={"status": "error", "message": "No editable fields were provided."})

    if service_update_func:
        try:
            logger.info(f"Batch saving {object_type} {record_id}: {valid_update_data}")
            updated = service_update_func(db, record_id, **valid_update_data)
            if not updated:
                return JSONResponse(status_code=404, content={"status": "error", "message": "Record not found."})
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error in batch save execution: {e}")
            return {"status": "error", "message": str(e)}
    
    return JSONResponse(status_code=404, content={"status": "error", "message": "Update function not found"})

@router.post("/import")
@handle_agent_errors
async def import_csv(
    object_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content = await file.read()
        decoded = content.decode("utf-8")
        from web.backend.app.services.import_service import ImportService
        await ImportService.import_csv(db, object_type, decoded)
        return RedirectResponse(url=f"/{object_type.lower()}s", status_code=303)
    except Exception as e:
        logger.error(f"Import error: {e}")
        return RedirectResponse(url=f"/{object_type.lower()}s?error={str(e)}", status_code=303)

@router.post("/seed")
@handle_agent_errors
async def seed_data(theme: str = Form(...), db: Session = Depends(get_db)):
    try:
        from web.backend.app.services.seed_service import SeedService
        await SeedService.generate_theme_data(db, theme, count=5)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        logger.error(f"Seed error: {e}")
        return RedirectResponse(url=f"/?error={str(e)}", status_code=303)

@router.get("/lookups/search")
async def lookup_search(
    q: str = "",
    type: str = "Account",
    db: Session = Depends(get_db)
):
    try:
        data = _active_lookup_records(db, type, q, limit=5)
        return {"results": [_serialize_lookup_result(type, item) for item in data]}
    except Exception as e:
        logger.error(f"Error in lookup search: {e}")
        return {"results": [], "error": str(e)}


@router.get("/lookups/recent")
async def lookup_recent(type: str = "Account", ids: str = "", db: Session = Depends(get_db)):
    try:
        requested_ids = [item.strip() for item in ids.split(",") if item.strip()]
        if not requested_ids:
            return {"results": []}
        if type == "Contact":
            active_rows = db.query(models.Contact).filter(models.Contact.id.in_(requested_ids), models.Contact.deleted_at == None).all()
        elif type == "Product":
            active_rows = db.query(models.Product).filter(models.Product.id.in_(requested_ids), models.Product.deleted_at == None).all()
        elif type == "Asset":
            active_rows = db.query(models.Asset).filter(models.Asset.id.in_(requested_ids), models.Asset.deleted_at == None).all()
        elif type in {"VehicleSpecification", "Brand"}:
            active_rows = db.query(models.VehicleSpecification).filter(models.VehicleSpecification.id.in_(requested_ids), models.VehicleSpecification.deleted_at == None, models.VehicleSpecification.record_type == "Brand").all()
        elif type == "Model":
            active_rows = db.query(models.Model).filter(models.Model.id.in_(requested_ids), models.Model.deleted_at == None).all()
        elif type in {"Message", "MessageSend"}:
            active_rows = db.query(models.MessageSend).filter(models.MessageSend.id.in_(requested_ids), models.MessageSend.deleted_at == None).all()
        elif type in {"MessageTemplate", "Template"}:
            active_rows = db.query(models.MessageTemplate).filter(models.MessageTemplate.id.in_(requested_ids), models.MessageTemplate.deleted_at == None).all()
        else:
            active_rows = []
        active_map = {row.id: _serialize_lookup_result(type, row) for row in active_rows}
        results = [active_map[item_id] for item_id in requested_ids if item_id in active_map]
        return {"results": results}
    except Exception as e:
        logger.error(f"Error validating recent lookups: {e}")
        return {"results": [], "error": str(e)}
