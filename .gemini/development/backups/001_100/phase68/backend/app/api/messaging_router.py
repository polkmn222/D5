from typing import Optional
import logging
import os
import uuid
from fastapi import APIRouter, Depends, Request, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from db.database import get_db
from ..services.opportunity_service import OpportunityService
from ..services.message_template_service import MessageTemplateService
from ..services.attachment_service import AttachmentService
from pydantic import BaseModel
from db.models import Contact, Opportunity, Model, MessageTemplate, Attachment
from ..services.messaging_service import MessagingService
from ..services.surem_service import SureMService
from ..core.templates import templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messaging", tags=["Messaging"])

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

import os
import shutil
import uuid

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
    if old_image_url and old_image_url.startswith("/static/uploads/message_templates/"):
        local_file = os.path.join("app", old_image_url.lstrip("/"))
        if os.path.exists(local_file):
            try:
                os.remove(local_file)
            except OSError:
                logger.warning(f"Failed to remove old template image file: {local_file}")

    old_attachment_id = getattr(existing, "attachment_id", None)
    if old_attachment_id:
        AttachmentService.delete(db, old_attachment_id)

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
        recommended_opps = OpportunityService.get_ai_recommendations(db, limit=20)
        
        results_data = []
        for opp in recommended_opps:
            contact = db.query(Contact).filter(Contact.id == opp.contact).first()
            mod = db.query(Model).filter(Model.id == opp.model).first() if opp.model else None
            
            results_data.append({
                "id": opp.id,
                "name": opp.name,
                "stage": opp.stage,
                "created_at": opp.created_at.strftime('%Y-%m-%d') if opp.created_at else '-',
                "contact_id": contact.id,
                "contact": {"name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "Unnamed", "phone": contact.phone},
                "model": {"name": mod.name} if mod else None
            })
            
        return results_data
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
        
        file_extension = os.path.splitext(file.filename)[1]
        if file_extension.lower() not in {".jpg", ".jpeg"}:
            return JSONResponse(status_code=400, content={"message": "Only JPG images under 500KB are allowed."})
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        file_content = await file.read()
        file_size = len(file_content)
        if file_size > 500 * 1024:
            return JSONResponse(status_code=400, content={"message": "Only JPG images under 500KB are allowed."})

        upload_dir = os.path.join("app", "static", "uploads", "message_templates")
        os.makedirs(upload_dir, exist_ok=True)
        local_path = os.path.join(upload_dir, unique_filename)
        with open(local_path, "wb") as f:
            f.write(file_content)
        image_url = f"/static/uploads/message_templates/{unique_filename}"

        upload_res = SureMService.upload_image(db, file_content, file.filename)
        image_key = None
        if upload_res.get("status") == "success":
            image_key = upload_res.get("data", {}).get("imageKey")
            # Important: Import the key value to logger (google/logger) to check if saved
            logger.info(f"SUREM MMS Image Key saved: {image_key} for file {file.filename}")
        else:
            logger.error(f"SUREM MMS Image Upload failed for {file.filename}: {upload_res}")

        # Create Attachment record with provider_key
        attachment = AttachmentService.create_attachment(
            db,
            name=file.filename,
            file_path=image_url,
            content_type=file.content_type,
            file_size=file_size,
            parent_type="MessageTemplate",
            provider_key=image_key
        )
        
        return {
            "attachment_id": attachment.id,
            "file_path": attachment.file_path,
            "image_url": image_url,
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
# pyright: reportMissingImports=false, reportAttributeAccessIssue=false, reportGeneralTypeIssues=false, reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalOperand=false, reportCallIssue=false
