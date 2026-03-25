from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Contact, MessageTemplate
from db.models import MessageSend
from web.backend.app.core.templates import templates
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.backend.app.utils.error_handler import handle_agent_errors
from web.message.backend.services.message_service import MessageService
from web.message.backend.services.message_template_service import MessageTemplateService

import logging

router = APIRouter()
logger = logging.getLogger(__name__)

MESSAGE_LIST_COLUMNS = ["name", "direction", "status", "created_at"]
MESSAGE_LIST_BUILTINS = (
    {"id": "message-all", "label": "All Messages", "source": "all"},
    {"id": "message-recent", "label": "Recently Viewed", "source": "recent"},
)
MESSAGE_PAGE_SIZE = 50


@router.get("/views")
@handle_agent_errors
async def list_message_views(db: Session = Depends(get_db)):
    views = LeadListViewService.list_views(db, MESSAGE_LIST_COLUMNS, object_type="Message", builtin_views=MESSAGE_LIST_BUILTINS)
    pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
    return {"views": views, "pinned_view_id": pinned_view_id}


@router.post("/views")
@handle_agent_errors
async def create_message_view(payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.create_view(db, payload, MESSAGE_LIST_COLUMNS, object_type="Message", builtin_views=MESSAGE_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.put("/views/{view_id}")
@handle_agent_errors
async def update_message_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.update_view(db, view_id, payload, MESSAGE_LIST_COLUMNS, object_type="Message", builtin_views=MESSAGE_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.delete("/views/{view_id}")
@handle_agent_errors
async def delete_message_view(view_id: str, db: Session = Depends(get_db)):
    try:
        LeadListViewService.delete_view(db, view_id, object_type="Message", builtin_views=MESSAGE_LIST_BUILTINS)
        return JSONResponse(content={"status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.post("/views/{view_id}/pin")
@handle_agent_errors
async def pin_message_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
    payload = payload or {}
    try:
        pinned_view_id = LeadListViewService.set_pinned_view(db, view_id, MESSAGE_LIST_COLUMNS, pinned=bool(payload.get("pinned", True)), object_type="Message", builtin_views=MESSAGE_LIST_BUILTINS)
        return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.get("/", response_class=HTMLResponse)
@handle_agent_errors
async def list_messages(request: Request, db: Session = Depends(get_db)):
    related_mode = request.query_params.get("related") == "1" or bool(request.query_params.get("back_to"))
    back_url = request.query_params.get("back_to") or "/messages"
    page = max(int(request.query_params.get("page", "1") or "1"), 1)
    filters = [MessageSend.deleted_at == None]
    contact_filter = request.query_params.get("contact")
    template_filter = request.query_params.get("template")
    if contact_filter:
        filters.append(MessageSend.contact == contact_filter)
        related_mode = True
    if template_filter:
        filters.append(MessageSend.template == template_filter)
        related_mode = True
    query = db.query(MessageSend).filter(*filters)
    total_items = query.count()
    total_pages = max((total_items + MESSAGE_PAGE_SIZE - 1) // MESSAGE_PAGE_SIZE, 1)
    if page > total_pages:
        page = total_pages
    msgs = (
        query
        .order_by(MessageSend.created_at.desc())
        .offset((page - 1) * MESSAGE_PAGE_SIZE)
        .limit(MESSAGE_PAGE_SIZE)
        .all()
    )
    contact_ids = {msg.contact for msg in msgs if msg.contact}
    template_ids = {msg.template for msg in msgs if msg.template}
    contact_map = {}
    template_map = {}
    if contact_ids:
        contact_map = {contact.id: contact for contact in db.query(Contact).filter(Contact.id.in_(contact_ids), Contact.deleted_at == None).all()}
    if template_ids:
        template_map = {template.id: template for template in db.query(MessageTemplate).filter(MessageTemplate.id.in_(template_ids), MessageTemplate.deleted_at == None).all()}
    items = []
    for m in msgs:
        contact = contact_map.get(m.contact) if m.contact else None
        template = template_map.get(m.template) if m.template else None
        contact_name = f"{contact.first_name} {contact.last_name}" if contact else "Unknown"
        template_name = template.name if template else "Custom Content"
        msg_type = template.record_type if template and template.record_type else "SMS"
        name_display = f"{contact_name} - {template_name} ({msg_type})"
        items.append({
            "id": m.id,
            "name": name_display,
            "direction": m.direction,
            "status": m.status,
            "created_at": m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else "",
            "edit_url": f"/messages/new-modal?id={m.id}",
            "_href": f"/messages/{m.id}",
        })

    if related_mode:
        new_query = []
        if contact_filter:
            new_query.append(f"contact={contact_filter}")
        if template_filter:
            new_query.append(f"template={template_filter}")
        new_url = "/messages/new-modal"
        if new_query:
            new_url += "?" + "&".join(new_query)
        return templates.TemplateResponse(request, "related/list_view.html", {
            "request": request,
            "page_title": "Messages",
            "items": items,
            "columns": MESSAGE_LIST_COLUMNS,
            "back_url": back_url,
            "new_url": new_url,
            "page_icon": "message",
            "show_actions": True,
        })

    saved_views = LeadListViewService.list_views(db, MESSAGE_LIST_COLUMNS, object_type="Message", builtin_views=MESSAGE_LIST_BUILTINS)
    saved_view_ids = {view["id"] for view in saved_views}
    pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
    requested_view = request.query_params.get("view")
    current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "message-all")

    return templates.TemplateResponse(request, "messages/list_view.html", {
        "request": request,
        "object_type": "Message",
        "plural_type": "messages",
        "items": items,
        "columns": MESSAGE_LIST_COLUMNS,
        "current_view": current_view,
        "list_view_options": [{"value": view["id"], "label": view["label"]} for view in saved_views],
        "saved_views": saved_views,
        "pinned_view_id": pinned_view_id,
        "list_view_storage_key": "d4_recent_messages",
        "pagination": {
            "page": page,
            "page_size": MESSAGE_PAGE_SIZE,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
            "prev_page": page - 1,
            "next_page": page + 1,
        },
    })


@router.post("/send")
@handle_agent_errors
async def send_message(
    request: Request,
    contact_id: str = Form(...),
    content: str = Form(None),
    template_id: str = Form(None),
    db: Session = Depends(get_db),
):
    from web.message.backend.services.messaging_service import MessagingService

    MessagingService.send_message(db, contact_id=contact_id, content=content, template_id=template_id)
    return RedirectResponse(url=f"/contacts/{contact_id}?success=Message+sent", status_code=303)


@router.get("/templates", response_class=HTMLResponse)
@handle_agent_errors
async def list_templates(request: Request, db: Session = Depends(get_db)):
    tmpls = MessageTemplateService.get_templates(db)
    return templates.TemplateResponse(request, "messages/templates_list.html", {"request": request, "items": tmpls})


@router.get("/{message_id}", response_class=HTMLResponse)
@handle_agent_errors
async def message_detail(request: Request, message_id: str, db: Session = Depends(get_db)):
    message = MessageService.get_message(db, message_id)
    if not message:
        return RedirectResponse(url="/messages?error=Message+not+found")

    contact = ContactService.get_contact(db, message.contact) if message.contact else None
    template = MessageTemplateService.get_template(db, message.template) if message.template else None
    contact_name = f"{contact.first_name} {contact.last_name}" if contact else ""
    template_name = template.name if template else ""
    details = {
        "Contact": contact_name,
        "Contact_Hidden_Ref": message.contact or "",
        "Template": template_name,
        "Template_Hidden_Ref": message.template or "",
        "Direction": message.direction or "",
        "Status": message.status or "",
        "Content": message.content or "",
    }

    record_name = contact_name or template_name or f"Message {message_id}"
    return templates.TemplateResponse(request, "messages/detail_view.html", {
        "request": request,
        "object_type": "Message",
        "plural_type": "messages",
        "record_id": message_id,
        "record_name": record_name,
        "details": details,
        "created_at": message.created_at,
        "updated_at": message.updated_at,
        "related_lists": [],
        "path": [],
        "is_followed": False,
    })
