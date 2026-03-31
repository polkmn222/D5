from typing import Optional
import logging
import os
from urllib.parse import urlparse, urlunparse
from fastapi import APIRouter, Depends, Request, File, UploadFile, Header
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
import httpx
from db.database import get_db
from web.backend.app.services.opportunity_service import OpportunityService
from web.message.backend.services.message_template_service import MessageTemplateService
from web.backend.app.services.attachment_service import AttachmentService
from web.backend.app.services.public_image_storage_service import PublicImageStorageService
from pydantic import BaseModel
from db.models import Contact, Opportunity, Model, MessageTemplate, Attachment
from web.message.backend.services.messaging_service import MessagingService
from web.message.backend.services.message_providers.factory import MessageProviderFactory
from web.message.backend.services.message_providers.base import MessageDispatchPayload
from web.backend.app.core.templates import templates
from ai_agent.llm.backend.recommendations import AIRecommendationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/messaging", tags=["Messaging"])
DEMO_UNAVAILABLE_MESSAGE = "Message service is unavailable. Contact the administrator."


def _serialize_messaging_recommendations(db: Session, recommended_opps, limit: Optional[int] = None):
    results_data = []
    for opp in recommended_opps:
        if limit is not None and len(results_data) >= limit:
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


def _load_default_recipient_rows(db: Session):
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


def _load_message_template_rows(db: Session):
    message_templates_query = db.query(MessageTemplate, Attachment)\
        .outerjoin(Attachment, MessageTemplate.attachment_id == Attachment.id)\
        .filter(MessageTemplate.deleted_at == None)\
        .all()

    templates_data = []
    for t, a in message_templates_query:
        image_url = t.image_url
        if image_url and "/static/uploads/templates/" in image_url:
            image_url = image_url.replace("/static/uploads/templates/", "/static/uploads/message_templates/")

        templates_data.append({
            "id": t.id,
            "name": t.name,
            "subject": "" if t.record_type == "SMS" else t.subject,
            "content": t.content,
            "record_type": t.record_type,
            "file_path": t.file_path,
            "attachment_id": t.attachment_id,
            "attachment": {
                "name": a.name,
                "size": a.file_size,
                "type": a.content_type
            } if a else None,
            "image_url": image_url
        })
    return templates_data

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

class RelayDispatchRequest(BaseModel):
    contact_id: str
    record_type: str = "SMS"
    content: str
    subject: Optional[str] = None
    template_id: Optional[str] = None
    attachment_id: Optional[str] = None
    attachment_path: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_provider_key: Optional[str] = None
    image_url: Optional[str] = None


def _demo_unavailable_response(reason: Optional[str] = None) -> dict:
    return {
        "available": False,
        "message": DEMO_UNAVAILABLE_MESSAGE,
        "reason": reason or "relay_unavailable",
    }


def _validate_bearer_token(authorization: Optional[str], expected_token: str) -> bool:
    incoming_token = (authorization or "").removeprefix("Bearer ").strip()
    return bool(expected_token) and incoming_token == expected_token


def _relay_target_provider() -> str:
    return os.getenv("RELAY_TARGET_PROVIDER", "").strip().lower() or "surem"


def _provider_ready_for_demo(provider_name: str) -> tuple[bool, Optional[str]]:
    if provider_name == "relay":
        return False, "relay_target_cannot_be_relay"
    if provider_name == "surem":
        required = {
            "SUREM_AUTH_userCode": os.getenv("SUREM_AUTH_userCode", "").strip() or os.getenv("SUREM_USER_CODE", "").strip(),
            "SUREM_AUTH_secretKey": os.getenv("SUREM_AUTH_secretKey", "").strip() or os.getenv("SUREM_SECRET_KEY", "").strip(),
            "SUREM_reqPhone": os.getenv("SUREM_reqPhone", "").strip() or os.getenv("SUREM_REQ_PHONE", "").strip(),
            "SUREM_TO": os.getenv("SUREM_TO", "").strip() or os.getenv("SUREM_FORCE_TO_NUMBER", "").strip(),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            return False, f"missing_demo_provider_env:{','.join(missing)}"
    if provider_name == "slack" and not os.getenv("SLACK_MESSAGE_WEBHOOK_URL", "").strip():
        return False, "missing_demo_provider_env:SLACK_MESSAGE_WEBHOOK_URL"
    return True, None


def _derive_demo_relay_health_url(endpoint: str) -> Optional[str]:
    endpoint = (endpoint or "").strip()
    if not endpoint:
        return None

    parsed = urlparse(endpoint)
    if not parsed.scheme or not parsed.netloc:
        return None

    relay_path = parsed.path.rstrip("/")
    if not relay_path.endswith("/messaging/relay-dispatch"):
        return None

    health_path = f"{relay_path[:-len('/relay-dispatch')]}/demo-relay-health"
    return urlunparse(parsed._replace(path=health_path, params="", query="", fragment=""))


def _check_remote_demo_relay_health(endpoint: str, token: str) -> dict:
    health_url = _derive_demo_relay_health_url(endpoint)
    if not health_url:
        return _demo_unavailable_response("invalid_relay_endpoint")

    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client() as client:
            response = client.get(health_url, headers=headers, timeout=3)
    except Exception as exc:
        logger.warning("Demo relay availability probe failed: %s", exc)
        return _demo_unavailable_response("relay_health_unreachable")

    if response.status_code >= 400:
        return _demo_unavailable_response(f"relay_health_http_{response.status_code}")

    try:
        payload = response.json()
    except ValueError:
        return _demo_unavailable_response("relay_health_invalid_json")

    if not payload.get("available"):
        return _demo_unavailable_response(payload.get("reason") or "relay_unavailable")

    return {
        "available": True,
        "message": "",
        "reason": None,
        "provider": payload.get("provider"),
        "mode": "relay",
    }

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

@router.get("/provider-status")
async def provider_status():
    try:
        return {"status": "success", "data": MessageProviderFactory.get_provider_status()}
    except Exception as e:
        logger.error(f"Error reading provider status: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@router.get("/demo-relay-health")
async def demo_relay_health(authorization: Optional[str] = Header(default=None)):
    expected_token = os.getenv("RELAY_MESSAGE_TOKEN", "").strip()
    if not expected_token:
        return JSONResponse(status_code=503, content=_demo_unavailable_response("relay_token_not_configured"))

    if not _validate_bearer_token(authorization, expected_token):
        return JSONResponse(status_code=403, content=_demo_unavailable_response("invalid_relay_token"))

    target_provider = _relay_target_provider()
    provider_ready, reason = _provider_ready_for_demo(target_provider)
    if not provider_ready:
        return JSONResponse(status_code=503, content=_demo_unavailable_response(reason))

    return {
        "available": True,
        "message": "",
        "reason": None,
        "provider": target_provider,
    }


@router.get("/demo-availability")
async def demo_availability():
    provider_name = MessageProviderFactory.get_provider_name()
    if provider_name != "relay":
        return {
            "available": True,
            "message": "",
            "reason": None,
            "mode": "direct",
            "provider": provider_name,
        }

    endpoint = os.getenv("RELAY_MESSAGE_ENDPOINT", "").strip()
    token = os.getenv("RELAY_MESSAGE_TOKEN", "").strip()
    if not endpoint:
        return _demo_unavailable_response("relay_endpoint_not_configured")
    if not token:
        return _demo_unavailable_response("relay_token_not_configured")

    relay_status = _check_remote_demo_relay_health(endpoint, token)
    relay_status["provider"] = relay_status.get("provider") or provider_name
    relay_status["mode"] = "relay"
    return relay_status

@router.post("/relay-dispatch")
async def relay_dispatch(
    data: RelayDispatchRequest,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    try:
        expected_token = os.getenv("RELAY_MESSAGE_TOKEN", "").strip()
        if not expected_token:
            return JSONResponse(status_code=500, content={"status": "error", "message": "RELAY_MESSAGE_TOKEN is not configured."})

        if not _validate_bearer_token(authorization, expected_token):
            return JSONResponse(status_code=403, content={"status": "error", "message": "Invalid relay token."})

        target_provider = _relay_target_provider()
        if target_provider == "relay":
            return JSONResponse(status_code=400, content={"status": "error", "message": "RELAY_TARGET_PROVIDER cannot be relay."})

        payload = MessageDispatchPayload(
            contact_id=data.contact_id,
            record_type=(data.record_type or "SMS").upper(),
            content=data.content,
            subject=data.subject,
            template_id=data.template_id,
            attachment_id=data.attachment_id,
            attachment_path=data.attachment_path,
            attachment_name=data.attachment_name,
            attachment_provider_key=data.attachment_provider_key,
            image_url=data.image_url,
        )
        provider_response = MessagingService._dispatch_payload(db, payload, provider_name_override=target_provider)
        return {"status": "success", "data": provider_response}
    except Exception as e:
        logger.error(f"Error in relay dispatch: {e}")
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


def _content_length(value: Optional[str]) -> int:
    return len((value or "").encode("utf-8"))


def _normalize_template_payload(data: TemplateCreate) -> TemplateCreate:
    record_type = (data.record_type or "SMS").upper()
    content_length = _content_length(data.content)

    if record_type == "SMS" and content_length > 90:
        record_type = "LMS"
    if record_type in {"LMS", "MMS"} and content_length > 2000:
        raise ValueError("LMS and MMS templates must be 2000 bytes or fewer.")
    if record_type == "MMS" and not data.attachment_id:
        raise ValueError("MMS templates require a JPG image under 500KB.")

    data.record_type = record_type
    data.subject = data.subject if record_type != "SMS" else None
    return data


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
        opportunities_data = _load_default_recipient_rows(db)
        templates_data = _load_message_template_rows(db)

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
        recommended_opps = AIRecommendationService.get_sendable_recommendations(db)
        return _serialize_messaging_recommendations(db, recommended_opps)
    except Exception as e:
        logger.error(f"Error getting messaging recommendations: {e}")
        return []


@router.get("/default_recipients")
async def get_default_recipients(db: Session = Depends(get_db)):
    try:
        """
        Returns the default list of opportunities that have a phone number (Filtering for non-null Models).
        """
        return _load_default_recipient_rows(db)
    except Exception as e:
        logger.error(f"Error getting default recipients: {e}")
        return []


@router.get("/ai-agent-compose-data")
async def get_ai_agent_compose_data(db: Session = Depends(get_db)):
    try:
        return {
            "default_recipients": _load_default_recipient_rows(db),
            "templates": _load_message_template_rows(db),
        }
    except Exception as e:
        logger.error(f"Error getting AI agent compose data: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.post("/templates/upload")
async def upload_template_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        """Uploads an image for a message template (MMS) and creates an Attachment record"""
        original_filename = file.filename or "template-image.jpg"
        file_content = await file.read()
        file_size = len(file_content)
        try:
            MessageTemplateService.validate_template_image_upload(
                filename=original_filename,
                content_type=file.content_type,
                file_size=file_size,
            )
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"message": str(exc)})
        if not file_content:
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
        data = _normalize_template_payload(data)
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
