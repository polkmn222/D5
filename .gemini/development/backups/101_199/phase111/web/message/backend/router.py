from typing import Optional
import logging
import os
from fastapi import APIRouter, Depends, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from db.database import get_db
from web.backend.app.services.opportunity_service import OpportunityService
from web.message.backend.services.message_template_service import MessageTemplateService
from web.backend.app.services.attachment_service import AttachmentService
from web.backend.app.services.public_image_storage_service import PublicImageStorageService
from pydantic import BaseModel
from db.models import Contact, Opportunity, Model, MessageTemplate, Attachment
from web.message.backend.services.messaging_service import MessagingService
from web.backend.app.core.templates import templates
from ai_agent.backend.recommendations import AIRecommendationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messaging", tags=["Messaging"])


def _serialize_messaging_recommendations(db: Session, recommended_opps, limit: int = 5):
    results_data = []
    for opp in recommended_opps:
        if len(results_data) >= limit:
            break

        contact = db.query(Contact).filter(Contact.id == opp.contact, Contact.deleted_at == None).first()
        if not contact or not contact.phone:
            continue

        if not getattr(opp, "model", None):
            continue

        mod = db.query(Model).filter(Model.id == opp.model).first()
        if not mod:
            continue

        results_data.append({
            "id": opp.id,
            "name": opp.name,
            "stage": opp.stage,
            "temperature": AIRecommendationService.normalize_temperature_label(getattr(opp, "temp_display", getattr(opp, "temperature", None))),
            "created_at": opp.created_at.strftime('%Y-%m-%d') if opp.created_at else '-',
            "contact_id": contact.id,
            "contact": {"name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "Unnamed", "phone": contact.phone},
            "model": {"name": mod.name},
        })
    return results_data

class MessageSendRequest(BaseModel):
    contact_id: str
    template_id: Optional[str] = None
    content: Optional[str] = None
    record_type: Optional[str] = "SMS"
    attachment_id: Optional[str] = None
    subject: Optional[str] = None

class BulkMessageRequest(BaseModel):
    contact_ids: list[str]
    template_id: Optional[str] = None
    content: Optional[str] = None
    record_type: Optional[str] = "SMS"
    attachment_id: Optional[str] = None
    subject: Optional[str] = None

@router.post("/send")
async def send_message_endpoint(data: MessageSendRequest, db: Session = Depends(get_db)):
    try:
        msg = MessagingService.send_message(
            db, 
            contact_id=data.contact_id, 
            template_id=data.template_id, 
            content=data.content,
            record_type=data.record_type,
            attachment_id=data.attachment_id,
            subject=data.subject
        )
        return {"status": "success", "message_id": msg.id}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.post("/bulk-send")
async def bulk_send_endpoint(data: BulkMessageRequest, db: Session = Depends(get_db)):
    try:
        count = MessagingService.bulk_send(
            db, 
            contact_ids=data.contact_ids, 
            template_id=data.template_id,
            content=data.content,
            record_type=data.record_type,
            attachment_id=data.attachment_id,
            subject=data.subject
        )
        return {"status": "success", "sent_count": count}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

class TemplateCreate(BaseModel):
    id: Optional[str] = None
    name: str
    subject: Optional[str] = None
    content: str
    record_type: str = "SMS" # Default to SMS
    file_path: Optional[str] = None
    attachment_id: Optional[str] = None
    image_url: Optional[str] = None


def _cleanup_template_image(db: Session, existing: MessageTemplate):
    old_image_url = getattr(existing, "image_url", None)
    old_attachment_id = getattr(existing, "attachment_id", None)
    if old_attachment_id:
        attachment = AttachmentService.get_attachment(db, old_attachment_id)
        if attachment:
            PublicImageStorageService.delete_image(
                file_path=getattr(attachment, "file_path", None),
                provider_key=getattr(attachment, "provider_key", None),
            )
        AttachmentService.delete(db, old_attachment_id)
    elif old_image_url:
        PublicImageStorageService.delete_image(file_path=old_image_url)

@router.get("/ui", response_class=HTMLResponse)
async def messaging_ui(request: Request, db: Session = Depends(get_db)):
    try:
        # Fetch only Contacts that have at least one Opportunity
        opp_contacts = db.query(Contact).join(Opportunity, Contact.id == Opportunity.contact).distinct().all()
        
        # Fetch opportunities with joined Contact and Model for display (Filtering for non-null Models)
        results = db.query(Opportunity, Contact, Model)\
            .join(Contact, Opportunity.contact == Contact.id)\
            .join(Model, Opportunity.model == Model.id)\
            .filter(Opportunity.deleted_at == None, Contact.deleted_at == None)\
            .filter(Contact.phone != None, Contact.phone != "")\
            .order_by(Opportunity.created_at.desc())\
            .all()

        opportunities_data = []
        for opp, contact, mod in results:
            opportunities_data.append({
                "id": opp.id,
                "name": opp.name,
                "stage": opp.stage,
                "created_at": opp.created_at,
                "contact_id": contact.id,
                "contact": {"name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "Unnamed", "phone": contact.phone},
                "model": {"name": mod.name} if mod else None
            })
        
        message_templates_query = db.query(MessageTemplate, Attachment)\
            .outerjoin(Attachment, MessageTemplate.attachment_id == Attachment.id)\
            .filter(MessageTemplate.deleted_at == None)\
            .all()
        
        templates_data = []
        for t, a in message_templates_query:
            templates_data.append({
                "id": t.id,
                "name": t.name,
                "subject": t.subject,
                "content": t.content,
                "record_type": t.record_type,
                "file_path": t.file_path,
                "attachment_id": t.attachment_id,
                "attachment": {
                    "name": a.name,
                    "size": a.file_size,
                    "type": a.content_type
                } if a else None,
                "image_url": t.image_url
            })
        
        return templates.TemplateResponse(request, "send_message.html", {
            "request": request,
            "contacts": opp_contacts,
            "opportunities": opportunities_data,
            "templates": templates_data
        })
    except Exception as e:
        logger.error(f"Error loading messaging UI: {e}")
        return RedirectResponse(url="/?error=Error+loading+messaging+UI")

@router.get("/recommendations")
async def get_messaging_recommendations(db: Session = Depends(get_db)):
    try:
        """
        Returns AI recommended opportunities (now pre-filtered for phone numbers by the service).
        """
        recommended_opps = AIRecommendationService.get_sendable_recommendations(db, limit=5, scan_limit=50)
        return _serialize_messaging_recommendations(db, recommended_opps, limit=5)
    except Exception as e:
        logger.error(f"Error getting messaging recommendations: {e}")
        return []


@router.get("/default_recipients")
async def get_default_recipients(db: Session = Depends(get_db)):
    try:
        """
        Returns the default list of opportunities that have a phone number (Filtering for non-null Models).
        """
        results = db.query(Opportunity, Contact, Model)\
            .join(Contact, Opportunity.contact == Contact.id)\
            .join(Model, Opportunity.model == Model.id)\
            .filter(Opportunity.deleted_at == None, Contact.deleted_at == None)\
            .filter(Contact.phone != None, Contact.phone != "")\
            .order_by(Opportunity.created_at.desc())\
            .all()

        opportunities_data = []
        for opp, contact, mod in results:
            opportunities_data.append({
                "id": opp.id,
                "name": opp.name,
                "stage": opp.stage,
                "created_at": opp.created_at.strftime('%Y-%m-%d') if opp.created_at else '-',
                "contact_id": contact.id,
                "contact": {"name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "Unnamed", "phone": contact.phone},
                "model": {"name": mod.name} if mod else None
            })
        return opportunities_data
    except Exception as e:
        logger.error(f"Error getting default recipients: {e}")
        return []

@router.post("/templates/upload")
async def upload_template_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        """Uploads an image for a message template (MMS) and creates an Attachment record"""
        allowed_types = {"image/jpeg", "image/jpg"}
        if file.content_type not in allowed_types:
             return JSONResponse(status_code=400, content={"message": "Only JPG images under 500KB are allowed."})
        
        original_filename = file.filename or "template-image.jpg"
        file_extension = os.path.splitext(original_filename)[1]
        if file_extension.lower() not in {".jpg", ".jpeg"}:
            return JSONResponse(status_code=400, content={"message": "Only JPG images under 500KB are allowed."})
        file_content = await file.read()
        file_size = len(file_content)
        if file_size > 500 * 1024:
            return JSONResponse(status_code=400, content={"message": "Only JPG images under 500KB are allowed."})

        stored_image = PublicImageStorageService.upload_message_template_image(
            filename=original_filename,
            file_content=file_content,
            content_type=file.content_type,
            folder="message_templates",
        )

        attachment = AttachmentService.create_attachment(
            db,
            name=original_filename,
            file_path=stored_image.file_path,
            content_type=file.content_type,
            file_size=file_size,
            parent_type="MessageTemplate",
            provider_key=stored_image.provider_key or ""
        )
        
        return {
            "attachment_id": attachment.id,
            "file_path": attachment.file_path,
            "image_url": attachment.file_path,
            "name": attachment.name,
            "size": attachment.file_size,
            "provider_key": attachment.provider_key
        }
    except Exception as e:
        logger.error(f"Error uploading template image: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.post("/templates")
async def create_template(data: TemplateCreate, db: Session = Depends(get_db)):
    try:
        if data.id:
            existing = MessageTemplateService.get_template(db, data.id)
            if existing:
                replacing_image = existing.attachment_id and existing.attachment_id != data.attachment_id
                removing_image = existing.attachment_id and (data.record_type != "MMS" or not data.attachment_id)
                if replacing_image or removing_image:
                    _cleanup_template_image(db, existing)
                return MessageTemplateService.update_template(db, data.id, 
                    name=data.name, 
                    subject=data.subject,
                    content=data.content, 
                    record_type=data.record_type,
                    file_path=data.file_path,
                    attachment_id=data.attachment_id,
                    image_url=data.image_url,
                )
        
        # Fallback to name check if no ID
        existing = db.query(MessageTemplate).filter(MessageTemplate.name == data.name).first()
        if existing:
            replacing_image = existing.attachment_id and existing.attachment_id != data.attachment_id
            removing_image = existing.attachment_id and (data.record_type != "MMS" or not data.attachment_id)
            if replacing_image or removing_image:
                _cleanup_template_image(db, existing)
            return MessageTemplateService.update_template(db, existing.id, 
                name=data.name,
                subject=data.subject,
                content=data.content, 
                record_type=data.record_type,
                file_path=data.file_path,
                attachment_id=data.attachment_id,
                image_url=data.image_url,
            )
            
        return MessageTemplateService.create_template(db, 
            name=data.name, 
            subject=data.subject,
            content=data.content, 
            record_type=data.record_type,
            file_path=data.file_path,
            attachment_id=data.attachment_id,
            image_url=data.image_url,
        )
    except Exception as e:
        logger.error(f"Error creating/updating template: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, db: Session = Depends(get_db)):
    try:
        existing = MessageTemplateService.get_template(db, template_id)
        if existing and (getattr(existing, "attachment_id", None) or getattr(existing, "image_url", None)):
            _cleanup_template_image(db, existing)
        MessageTemplateService.delete_template(db, template_id)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
