from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, Body
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

from db.database import get_db
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.message.backend.services.message_template_service import MessageTemplateService
from web.backend.app.services.attachment_service import AttachmentService
from web.backend.app.services.public_image_storage_service import PublicImageStorageService
from web.backend.app.core.templates import templates
from web.backend.app.utils.error_handler import handle_agent_errors
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
MESSAGE_TEMPLATE_LIST_COLUMNS = ["name", "subject", "content", "type"]
MESSAGE_TEMPLATE_LIST_BUILTINS = (
    {"id": "template-all", "label": "All Templates", "source": "all"},
    {"id": "template-recent", "label": "Recently Viewed", "source": "recent"},
)


def _remove_template_image(db: Session, template) -> None:
    attachment_id = getattr(template, "attachment_id", None)
    if attachment_id:
        attachment = AttachmentService.get_attachment(db, attachment_id)
        if attachment:
            PublicImageStorageService.delete_image(
                file_path=getattr(attachment, "file_path", None),
                provider_key=getattr(attachment, "provider_key", None),
            )
        AttachmentService.delete(db, attachment_id)
    elif getattr(template, "image_url", None):
        PublicImageStorageService.delete_image(getattr(template, "image_url", None))

# --- MESSAGE TEMPLATES ---
@router.get("/views")
@handle_agent_errors
async def list_message_template_views(db: Session = Depends(get_db)):
    views = LeadListViewService.list_views(db, MESSAGE_TEMPLATE_LIST_COLUMNS, object_type="MessageTemplate", builtin_views=MESSAGE_TEMPLATE_LIST_BUILTINS)
    pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
    return {"views": views, "pinned_view_id": pinned_view_id}


@router.post("/views")
@handle_agent_errors
async def create_message_template_view(payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.create_view(db, payload, MESSAGE_TEMPLATE_LIST_COLUMNS, object_type="MessageTemplate", builtin_views=MESSAGE_TEMPLATE_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.put("/views/{view_id}")
@handle_agent_errors
async def update_message_template_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.update_view(db, view_id, payload, MESSAGE_TEMPLATE_LIST_COLUMNS, object_type="MessageTemplate", builtin_views=MESSAGE_TEMPLATE_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.delete("/views/{view_id}")
@handle_agent_errors
async def delete_message_template_view(view_id: str, db: Session = Depends(get_db)):
    try:
        LeadListViewService.delete_view(db, view_id, object_type="MessageTemplate", builtin_views=MESSAGE_TEMPLATE_LIST_BUILTINS)
        return JSONResponse(content={"status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.post("/views/{view_id}/pin")
@handle_agent_errors
async def pin_message_template_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
    payload = payload or {}
    try:
        pinned_view_id = LeadListViewService.set_pinned_view(db, view_id, MESSAGE_TEMPLATE_LIST_COLUMNS, pinned=bool(payload.get("pinned", True)), object_type="MessageTemplate", builtin_views=MESSAGE_TEMPLATE_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


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
        saved_views = LeadListViewService.list_views(db, MESSAGE_TEMPLATE_LIST_COLUMNS, object_type="MessageTemplate", builtin_views=MESSAGE_TEMPLATE_LIST_BUILTINS)
        saved_view_ids = {view["id"] for view in saved_views}
        pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
        requested_view = request.query_params.get("view")
        current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "template-all")
        return templates.TemplateResponse(request, "message_templates/list_view.html", {
            "request": request,
            "object_type": "MessageTemplate",
            "plural_type": "message_templates",
            "items": items,
            "columns": MESSAGE_TEMPLATE_LIST_COLUMNS,
            "current_view": current_view,
            "list_view_options": [{"value": view["id"], "label": view["label"]} for view in saved_views],
            "saved_views": saved_views,
            "pinned_view_id": pinned_view_id,
            "list_view_storage_key": "d4_recent_message_templates",
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
        template = MessageTemplateService.get_template(db, template_id)
        if not template:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Template not found"})

        filename = file.filename or "template-upload.bin"
        file_content = await file.read()
        stored_image = PublicImageStorageService.upload_message_template_image(
            filename=filename,
            file_content=file_content,
            content_type=file.content_type or "application/octet-stream",
            folder="message_templates",
        )

        if getattr(template, "attachment_id", None) or getattr(template, "image_url", None):
            _remove_template_image(db, template)

        attachment = AttachmentService.create_attachment(
            db,
            name=filename,
            file_path=stored_image.file_path,
            content_type=file.content_type,
            file_size=len(file_content),
            parent_id=template_id,
            parent_type="MessageTemplate",
            provider_key=stored_image.provider_key or "",
        )
        template.file_path = stored_image.file_path
        template.image_url = stored_image.file_path
        template.attachment_id = attachment.id
        db.commit()
        db.refresh(template)

        return {"status": "success", "image_url": stored_image.file_path, "name": filename}
    except Exception as e:
        logger.error(f"Error uploading file for template {template_id}: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.post("/{template_id}/clear-image")
async def clear_template_image(template_id: str, db: Session = Depends(get_db)):
    try:
        template = MessageTemplateService.get_template(db, template_id)
        if not template:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Template not found"})
        _remove_template_image(db, template)
        template.image_url = ""
        template.file_path = ""
        template.attachment_id = None
        db.commit()
        db.refresh(template)
        return {"status": "success", "message": "Image removed"}
    except Exception as e:
        logger.error(f"Error removing image for template {template_id}: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
