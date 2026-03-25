from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from db.database import get_db
from web.message.backend.services.message_service import MessageService
from web.message.backend.services.message_template_service import MessageTemplateService
from web.backend.app.services.attachment_service import AttachmentService
from web.backend.app.services.contact_service import ContactService
from web.backend.app.core.templates import templates
from web.backend.app.utils.error_handler import handle_agent_errors
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# --- MESSAGES ---
@router.get("/", response_class=HTMLResponse)
@handle_agent_errors
async def list_messages(request: Request, db: Session = Depends(get_db)):
    msgs = MessageService.get_messages(db)
    items = []
    for m in msgs:
        contact = ContactService.get_contact(db, m.contact) if m.contact else None
        template = MessageTemplateService.get_template(db, m.template) if m.template else None
        
        contact_name = f"{contact.first_name} {contact.last_name}" if contact else "Unknown"
        template_name = template.name if template else "Custom Content"
        msg_type = template.record_type if template and template.record_type else "SMS"
        name_display = f"{contact_name} - {template_name} ({msg_type})"
        
        items.append({
            "id": m.id,
            "name": name_display,
            "direction": m.direction,
            "status": m.status,
            "created_at": m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else ""
        })
    columns = ["name", "direction", "status", "created_at"]
    return templates.TemplateResponse(request, "messages/list_view.html", {
        "request": request,
        "object_type": "Message",
        "plural_type": "messages",
        "items": items,
        "columns": columns
    })

@router.post("/send")
@handle_agent_errors
async def send_message(
    request: Request,
    contact_id: str = Form(...),
    content: str = Form(None),
    template_id: str = Form(None),
    db: Session = Depends(get_db)
):
    from web.message.backend.services.messaging_service import MessagingService
    MessagingService.send_message(db, contact_id=contact_id, content=content, template_id=template_id)
    return RedirectResponse(url=f"/contacts/{contact_id}?success=Message+sent", status_code=303)

# --- TEMPLATES ---
@router.get("/templates", response_class=HTMLResponse)
@handle_agent_errors
async def list_templates(request: Request, db: Session = Depends(get_db)):
    tmpls = MessageTemplateService.get_templates(db)
    return templates.TemplateResponse(request, "messages/templates_list.html", {"request": request, "items": tmpls})
