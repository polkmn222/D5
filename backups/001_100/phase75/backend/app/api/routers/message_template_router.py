from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from db.database import get_db
from backend.app.services.message_template_service import MessageTemplateService
from backend.app.services.attachment_service import AttachmentService
from backend.app.core.templates import templates
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

# --- MESSAGE TEMPLATES ---
@router.get("/new-modal")
async def new_template_modal_base(request: Request, id: str = None, db: Session = Depends(get_db)):
    try:
        return RedirectResponse(url=f"/message_templates/new?id={id}" if id else "/message_templates/new")
    except Exception as e:
        logger.error(f"New template modal error: {e}")
        return RedirectResponse(url=f"/message_templates?error=Error+opening+modal:+{str(e).replace(' ', '+')}")

@router.get("/")
async def list_templates(request: Request, db: Session = Depends(get_db)):
    try:
        templates_data = MessageTemplateService.get_templates(db)
        items = []
        for t in templates_data:
            items.append({
                "id": t.id,
                "name": t.name if t.name else "",
                "subject": t.subject if t.subject else "",
                "content": t.content if t.content else "",
                "type": t.record_type if hasattr(t, 'record_type') and t.record_type else "SMS",
                "edit_url": f"/message_templates/new-modal?id={t.id}"
            })
        columns = ["name", "subject", "content", "type"]
        return templates.TemplateResponse(request, "message_templates/list_view.html", {
            "request": request, "object_type": "MessageTemplate", "plural_type": "message_templates",
            "items": items, "columns": columns
        })
    except Exception as e:
        logger.error(f"List templates error: {e}")
        return RedirectResponse(url=f"/?error=Error+loading+templates:+{str(e).replace(' ', '+')}")

@router.get("/{template_id}")
async def template_detail(request: Request, template_id: str, db: Session = Depends(get_db)):
    try:
        t = MessageTemplateService.get_template(db, template_id)
        if not t: return RedirectResponse(url="/message_templates?error=Template+not+found")
        
        # Atomization: Decouple from generic Attachment system
        # We only care about t.image_url now
        
        details = {
            "Name": t.name if t.name else "",
            "Type": t.record_type if t.record_type else "",
            "Subject": t.subject if t.subject else "",
            "Content": t.content if t.content else "",
            "Image": t.image_url if t.image_url else ""
        }
        
        # No related_lists for attachments anymore in templates (Atomization)
        related_lists = []

        return templates.TemplateResponse(request, "message_templates/detail_view.html", {
            "request": request, "object_type": "MessageTemplate", "plural_type": "message_templates",
            "record_id": template_id, "record_name": t.name if t.name else "", "details": details,
            "created_at": t.created_at, "updated_at": t.updated_at, "related_lists": related_lists
        })
    except Exception as e:
        logger.error(f"Error loading template detail: {e}")
        return RedirectResponse(url="/message_templates?error=An+unexpected+error+occurred.+Please+try+again")

@router.post("/")
async def create_template_route(
    name: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    record_type: Optional[str] = Form("SMS"),
    db: Session = Depends(get_db)
):
    try:
        # Support both 'content' and 'description' from different form versions
        # We check for str type to avoid Form objects when called directly in tests
        c_val = content if isinstance(content, str) else None
        d_val = description if isinstance(description, str) else None
        content_val = c_val or d_val
        
        update_data = {"name": name, "subject": subject, "content": content_val, "record_type": record_type}
        # Filter out None and Form objects to avoid IntegrityError on NOT NULL columns if field wasn't in form
        update_data = {k: v for k, v in update_data.items() if isinstance(v, str)}
        
        t = MessageTemplateService.create_template(db, **update_data)
        return RedirectResponse(url=f"/message_templates/{t.id}?success=Record+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Create Template error: {e}")
        return RedirectResponse(url=f"/message_templates?error=Error+creating+template:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{template_id}")
async def update_template_route(
    template_id: str,
    name: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    record_type: Optional[str] = Form("SMS"),
    db: Session = Depends(get_db)
):
    try:
        # Support both 'content' and 'description' from different form versions
        # We check for str type to avoid Form objects when called directly in tests
        c_val = content if isinstance(content, str) else None
        d_val = description if isinstance(description, str) else None
        content_val = c_val or d_val
        
        update_data = {"name": name, "subject": subject, "content": content_val, "record_type": record_type}
        # Filter out None and Form objects to prevent overwriting with NULL and hitting NOT NULL constraints
        update_data = {k: v for k, v in update_data.items() if isinstance(v, str)}
        
        MessageTemplateService.update_template(db, template_id, **update_data)
        return RedirectResponse(url=f"/message_templates/{template_id}?success=Record+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Update Template error: {e}")
        return RedirectResponse(url=f"/message_templates/{template_id}?error=Error+updating+template:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{template_id}/delete")
async def delete_template_route(request: Request, template_id: str, db: Session = Depends(get_db)):
    try:
        MessageTemplateService.delete_template(db, template_id)
        if "application/json" in request.headers.get("Accept", ""):
            return {"status": "success", "message": "Record deleted successfully"}
        return RedirectResponse(url="/message_templates?success=Record+deleted+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Delete Template error: {e}")
        return RedirectResponse(url=f"/message_templates?error=Error+deleting+template:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{template_id}/upload")
async def template_upload(template_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        upload_dir = "app/static/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        # Update template directly with image_url (Atomization)
        # Dedicated upload function logic
        image_url = f"/static/uploads/{file.filename}"
        MessageTemplateService.update_image_url(db, template_id, image_url=image_url)
        
        return {"status": "success", "image_url": image_url, "name": file.filename}
    except Exception as e:
        logger.error(f"Error uploading file for template {template_id}: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.post("/{template_id}/clear-image")
async def clear_template_image(template_id: str, db: Session = Depends(get_db)):
    try:
        MessageTemplateService.update_image_url(db, template_id, image_url="")
        return {"status": "success", "message": "Image removed"}
    except Exception as e:
        logger.error(f"Error removing image for template {template_id}: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
