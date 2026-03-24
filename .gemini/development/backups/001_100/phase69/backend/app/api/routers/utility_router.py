from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from db.database import get_db
from backend.app.utils.error_handler import handle_agent_errors
from backend.app.services.contact_service import ContactService
from backend.app.services.lead_service import LeadService
from backend.app.services.product_service import ProductService
from backend.app.services.opportunity_service import OpportunityService
from backend.app.services.asset_service import AssetService

from backend.app.services.model_service import ModelService
from backend.app.services.vehicle_spec_service import VehicleSpecService as VehicleSpecificationService
from backend.app.services.import_service import ImportService
from backend.app.services.message_template_service import MessageTemplateService
from db import models
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

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
            "message_templates": (MessageTemplateService, MessageTemplateService.get_template)
        }

        record_tuple = object_type_map.get(object_type)

        if not record_tuple:
            logger.error(f"Object type {object_type} not supported for inline save")
            return {"status": "error", "message": "Object type not supported"}
            
        service, get_method = record_tuple
        record = get_method(db, record_id)
        
        if record:
            field_norm = field_name.lower()
            if field_norm == "contact_hidden_ref": update_data = {"contact": value}
            elif field_norm == "opportunity_hidden_ref": update_data = {"opportunity": value}
            elif field_norm == "brand_hidden_ref": update_data = {"brand": value}
            elif field_norm == "model_hidden_ref": update_data = {"model": value}
            elif field_norm == "product_hidden_ref": update_data = {"product": value}
            elif field_norm == "asset_hidden_ref": update_data = {"asset": value}
            elif field_norm == "message_hidden_ref": update_data = {"message": value}
            elif field_norm == "template_hidden_ref": update_data = {"template": value}
            elif field_norm == "opportunity_name": 
                update_data = {"name": value}
            elif field_norm == "name" and object_type in ["leads", "contacts"]:
                parts = value.split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""
                update_data = {"first_name": first_name, "last_name": last_name}
            elif field_norm == "type" and object_type == "message_templates":
                update_data = {"record_type": value}
            else:
                if field_norm in ["amount", "price", "budget", "base_price", "probability"]:
                    try:
                        value = str(value).replace(",", "").replace("₩", "").strip()
                        if not value: value = "0"
                    except:
                        pass
                update_data = {field_norm: value}

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
        "message_templates": (MessageTemplateService, MessageTemplateService.get_template)
    }

    record_tuple = object_type_map.get(object_type)
    if not record_tuple:
        return {"status": "error", "message": "Object type not supported"}
        
    service, get_method = record_tuple
    record = get_method(db, record_id)
    if not record:
        return {"status": "error", "message": "Record not found"}

    update_data = {}
    for field, value in data.items():
        field_norm = field.lower().replace(" ", "_")
        
        if field_norm == "contact_hidden_ref": update_data["contact"] = value
        elif field_norm == "opportunity_hidden_ref": update_data["opportunity"] = value
        elif field_norm == "brand_hidden_ref": update_data["brand"] = value
        elif field_norm == "model_hidden_ref": update_data["model"] = value
        elif field_norm == "product_hidden_ref": update_data["product"] = value
        elif field_norm == "asset_hidden_ref": update_data["asset"] = value
        elif field_norm == "message_hidden_ref": update_data["message"] = value
        elif field_norm == "template_hidden_ref": update_data["template"] = value
        elif field_norm == "opportunity_name": 
            update_data["name"] = value
        elif field_norm == "name" and object_type in ["leads", "contacts"]:
            parts = value.split(" ", 1)
            update_data["first_name"] = parts[0]
            update_data["last_name"] = parts[1] if len(parts) > 1 else ""
        elif field_norm == "type" and object_type == "message_templates":
            update_data["record_type"] = value
        elif field_norm == "description" and object_type == "message_templates":
            update_data["content"] = value
        else:
            if field_norm in ["amount", "price", "budget", "base_price", "probability"]:
                try:
                    value = str(value).replace(",", "").replace("₩", "").strip()
                    if not value: value = "0"
                except:
                    pass
            update_data[field_norm] = value

    # Identify update function
    if object_type == "vehicle_specifications": service_update_func = service.update_vehicle_spec
    elif object_type == "opportunities": service_update_func = service.update_opportunity
    elif object_type == "leads": service_update_func = service.update_lead
    elif object_type == "contacts": service_update_func = service.update_contact
    elif object_type == "products": service_update_func = service.update_product
    elif object_type == "models": service_update_func = service.update_model
    elif object_type == "message_templates": service_update_func = service.update_template
    else:
        singular = object_type.rstrip('s')
        if object_type.endswith('ies'): singular = object_type[:-3] + 'y'
        service_update_func = getattr(service, f"update_{singular}", None)

    if service_update_func:
        try:
            logger.info(f"Batch saving {object_type} {record_id}: {update_data}")
            service_update_func(db, record_id, **update_data)
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
        from backend.app.services.import_service import ImportService
        await ImportService.import_csv(db, object_type, decoded)
        return RedirectResponse(url=f"/{object_type.lower()}s", status_code=303)
    except Exception as e:
        logger.error(f"Import error: {e}")
        return RedirectResponse(url=f"/{object_type.lower()}s?error={str(e)}", status_code=303)

@router.post("/seed")
@handle_agent_errors
async def seed_data(theme: str = Form(...), db: Session = Depends(get_db)):
    try:
        from backend.app.services.seed_service import SeedService
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
        results = []
        limit = 5
        
        if type == "Contact":
            # Use string concatenation for SQLite compatibility
            q_filter = f"%{q}%"
            data = db.query(models.Contact).filter(
                or_(
                    (models.Contact.first_name + " " + models.Contact.last_name).ilike(q_filter),
                    models.Contact.name.ilike(q_filter)
                )
            ).limit(limit).all()
            for item in data: 
                display_name = item.name if item.name else f"{item.first_name} {item.last_name}"
                results.append({"id": item.id, "name": display_name, "type": "Contact"})
        elif type == "Product":
            data = db.query(models.Product).filter(models.Product.name.ilike(f"%{q}%")).limit(limit).all()
            for item in data: results.append({"id": item.id, "name": item.name, "type": "Product"})
        elif type == "Asset":
            data = db.query(models.Asset).filter(models.Asset.name.ilike(f"%{q}%")).limit(limit).all()
            for item in data: results.append({"id": item.id, "name": item.name, "type": "Asset", "price": item.price})
        elif type == "VehicleSpecification" or type == "Brand":
            data = db.query(models.VehicleSpecification).filter(models.VehicleSpecification.name.ilike(f"%{q}%")).limit(limit).all()
            for item in data: results.append({"id": item.id, "name": item.name, "type": "Brand"})
        elif type == "Model":
            data = db.query(models.Model).filter(models.Model.name.ilike(f"%{q}%")).limit(limit).all()
            for item in data: results.append({"id": item.id, "name": item.name, "type": "Model"})
        elif type == "Message" or type == "MessageSend":
            data = db.query(models.MessageSend).filter(models.MessageSend.content.ilike(f"%{q}%")).limit(limit).all()
            for item in data: 
                display = item.content[:50] + "..." if len(item.content) > 50 else item.content
                results.append({"id": item.id, "name": display, "type": "MessageSend"})
        elif type == "MessageTemplate" or type == "Template":
            data = db.query(models.MessageTemplate).filter(models.MessageTemplate.name.ilike(f"%{q}%")).limit(limit).all()
            for item in data: results.append({"id": item.id, "name": item.name, "type": "MessageTemplate"})

        return {"results": results}
    except Exception as e:
        logger.error(f"Error in lookup search: {e}")
        return {"results": [], "error": str(e)}


@router.get("/api/surem/test-auth")
async def test_surem_auth(db: Session = Depends(get_db)):
    from backend.app.services.surem_service import SureMService
    try:
        logger.info("Testing SureM Authentication...")
        result = SureMService.debug_auth_status(db)
        token = SureMService.get_access_token(db) if result.get("status") == "success" else None
        if token:
            result["token_preview"] = token[:10] + "..." + token[-10:] if len(token) > 20 else token
        return result
    except Exception as e:
        logger.error(f"Error during SureM auth test: {e}")
        return {"status": "error", "message": str(e)}
