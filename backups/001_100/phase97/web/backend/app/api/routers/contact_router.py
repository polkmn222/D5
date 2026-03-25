from typing import Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from db.database import get_db
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.asset_service import AssetService
from web.backend.app.core.templates import templates
from web.backend.app.core.enums import Gender
from web.backend.app.utils.error_handler import handle_agent_errors
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{contact_id}", response_class=HTMLResponse)
@handle_agent_errors
async def contact_detail(request: Request, contact_id: str, db: Session = Depends(get_db)):
    logger.info(f"Accessing Contact Detail: {contact_id}")
    contact = ContactService.get_contact(db, contact_id)
    if not contact:
        return RedirectResponse(url="/contacts?error=Contact+not+found")
    
    details = {
        "First Name": contact.first_name if contact.first_name else "",
        "Last Name": contact.last_name if contact.last_name else "",
        "Full Name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or "",
        "Email": contact.email if contact.email else "",
        "Phone": contact.phone if contact.phone else "",
        "Website": contact.website if contact.website else "",
        "Tier": contact.tier if contact.tier else "",
        "Created Date": contact.created_at.strftime("%Y-%m-%d %H:%M") if contact.created_at else ""
    }
    
    # Related Assets
    assets = AssetService.get_assets(db, contact=contact_id)
    related_lists = []
    if assets:
        related_lists.append({
            "title": "Assets",
            "columns": ["name", "vin", "status"],
            "items": [{"name": a.name, "vin": a.vin, "status": a.status} for a in assets]
        })

    return templates.TemplateResponse(request, "contacts/detail_view.html", {
        "request": request, "object_type": "Contact", "plural_type": "contacts",
        "record_id": contact_id, "record_name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}",
        "details": details, "created_at": contact.created_at,
        "updated_at": contact.updated_at, "related_lists": related_lists
    })

@router.get("/", response_class=HTMLResponse)
@handle_agent_errors
async def list_contacts(request: Request, db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    items = []
    for c in contacts:
        items.append({
            "id": c.id,
            "name": f"{c.first_name} {c.last_name}",
            "email": c.email,
            "phone": c.phone,
            "created": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
            "edit_url": f"/contacts/new?id={c.id}"
        })
    columns = ["name", "email", "phone", "created"]
    return templates.TemplateResponse(request, "contacts/list_view.html", {
        "request": request, 
        "object_type": "Contact", 
        "plural_type": "contacts",
        "items": items, 
        "columns": columns
    })

@router.post("/")
@handle_agent_errors
async def create_contact(
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    tier: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    contact = ContactService.create_contact(
        db, first_name=first_name, last_name=last_name, gender=gender,
        email=email, phone=phone, website=website,
        tier=tier, description=description
    )
    return RedirectResponse(url=f"/contacts/{contact.id}?success=Record+created+successfully", status_code=303)

@router.post("/{contact_id}")
@handle_agent_errors
async def update_contact(
    request: Request,
    contact_id: str,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    tier: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    ContactService.update_contact(
        db, contact_id, first_name=first_name, last_name=last_name, 
        gender=gender, email=email, phone=phone,
        website=website, tier=tier, description=description
    )
    return RedirectResponse(url=f"/contacts/{contact_id}" + "?success=Record+updated+successfully", status_code=303)

@router.post("/{contact_id}/update")
@handle_agent_errors
async def update_contact_legacy(
    request: Request,
    contact_id: str,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    tier: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    return await update_contact(request, contact_id, first_name, last_name, gender, email, phone, website, tier, description, db)

@router.post("/{contact_id}/batch-save")
@handle_agent_errors
async def batch_save_contact(contact_id: str, updates: dict, db: Session = Depends(get_db)):
    """Handles JSON batch updates from inline editing."""
    # Clean keys (remove underscores/spaces and match model)
    clean_updates = {}
    for k, v in updates.items():
        key = k.lower().replace(" ", "_")
        clean_updates[key] = v
    
    ContactService.update_contact(db, contact_id, **clean_updates)
    return {"status": "success"}

@router.post("/{contact_id}/delete")
@handle_agent_errors
async def delete_contact(request: Request, contact_id: str, db: Session = Depends(get_db)):
    try:
        success = ContactService.delete_contact(db, contact_id)
        if success:
            return RedirectResponse(url="/contacts?success=Contact+deleted+successfully", status_code=303)
        return RedirectResponse(url=f"/contacts?error=Contact+not+found", status_code=303)
    except Exception as e:
        logger.error(f"Delete Contact error: {e}")
        return RedirectResponse(url=f"/contacts?error=Error+deleting+contact:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{contact_id}/restore")
async def restore_contact_endpoint(contact_id: str, db: Session = Depends(get_db)):
    try:
        contact = ContactService.restore_contact(db, contact_id)
        if contact:
            return {"status": "success"}
        return {"status": "error", "message": "Contact not found"}
    except Exception as e:
        logger.error(f"Restore Contact error: {e}")
        return RedirectResponse(url=f"/contacts?error=Error+restoring+contact:+{str(e).replace(' ', '+')}", status_code=303)
