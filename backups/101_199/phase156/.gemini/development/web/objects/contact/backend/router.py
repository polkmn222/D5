from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import logging

from db.database import get_db
from db.models import Contact, Asset
from web.objects.contact.backend.service import ContactService
from web.backend.app.services.asset_service import AssetService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.core.backend.core.templates import templates
from web.core.backend.core.enums import Gender
from web.core.backend.utils.error_handler import handle_agent_errors
from web.message.backend.services.message_service import MessageService

logger = logging.getLogger(__name__)

class ContactRouter:
    """
    ContactRouter manages all routes for the Contact object.
    It uses a single APIRouter instance and defines routes as class methods.
    """
    router = APIRouter()
    CONTACT_LIST_COLUMNS = ["name", "email", "phone", "tier", "created"]
    CONTACT_LIST_BUILTINS = (
        {"id": "contact-all", "label": "All Contacts", "source": "all"},
        {"id": "contact-recent", "label": "Recently Viewed", "source": "recent"},
    )

    @staticmethod
    @router.get("/views")
    @handle_agent_errors
    async def list_contact_views(db: Session = Depends(get_db)):
        try:
            views = LeadListViewService.list_views(
                db,
                ContactRouter.CONTACT_LIST_COLUMNS,
                object_type="Contact",
                builtin_views=ContactRouter.CONTACT_LIST_BUILTINS,
            )
            pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
            return {"views": views, "pinned_view_id": pinned_view_id}
        except Exception as e:
            logger.error(f"Error listing contact views: {str(e)}")
            return {"views": [], "pinned_view_id": None}

    @staticmethod
    @router.post("/views")
    @handle_agent_errors
    async def create_contact_view(payload: dict = Body(...), db: Session = Depends(get_db)):
        try:
            view = LeadListViewService.create_view(
                db,
                payload,
                ContactRouter.CONTACT_LIST_COLUMNS,
                object_type="Contact",
                builtin_views=ContactRouter.CONTACT_LIST_BUILTINS,
            )
            return JSONResponse(content={"status": "success", "view": view})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error creating contact view: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.put("/views/{view_id}")
    @handle_agent_errors
    async def update_contact_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
        try:
            view = LeadListViewService.update_view(
                db,
                view_id,
                payload,
                ContactRouter.CONTACT_LIST_COLUMNS,
                object_type="Contact",
                builtin_views=ContactRouter.CONTACT_LIST_BUILTINS,
            )
            return JSONResponse(content={"status": "success", "view": view})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error updating contact view {view_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.delete("/views/{view_id}")
    @handle_agent_errors
    async def delete_contact_view(view_id: str, db: Session = Depends(get_db)):
        try:
            LeadListViewService.delete_view(db, view_id, object_type="Contact")
            return JSONResponse(content={"status": "success"})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error deleting contact view {view_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.post("/views/{view_id}/pin")
    @handle_agent_errors
    async def pin_contact_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
        try:
            payload = payload or {}
            pinned_view_id = LeadListViewService.set_pinned_view(
                db,
                view_id,
                ContactRouter.CONTACT_LIST_COLUMNS,
                pinned=bool(payload.get("pinned", True)),
                object_type="Contact",
                builtin_views=ContactRouter.CONTACT_LIST_BUILTINS,
            )
            return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error pinning contact view {view_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.get("/{contact_id}", response_class=HTMLResponse)
    @handle_agent_errors
    async def contact_detail(request: Request, contact_id: str, db: Session = Depends(get_db)):
        try:
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
            
            related_lists = []

            opportunities = OpportunityService.get_by_contact(db, contact_id)
            if opportunities:
                related_lists.append({
                    "title": "Opportunities",
                    "columns": ["Name", "Stage", "Amount"],
                    "icon": "opportunity",
                    "new_url": f"/opportunities/new-modal?contact={contact_id}",
                    "view_all_url": f"/opportunities?contact={contact_id}&related=1&back_to=/contacts/{contact_id}?tab=related",
                    "total_count": len(opportunities),
                    "items": [{
                        "name": opportunity.name,
                        "stage": opportunity.stage,
                        "amount": f"{opportunity.amount:,}" if opportunity.amount else "0",
                        "_href": f"/opportunities/{opportunity.id}",
                    } for opportunity in opportunities[:5]]
                })

            messages = MessageService.get_messages(db, contact=contact_id)
            if messages:
                related_lists.append({
                    "title": "Messages",
                    "columns": ["Name", "Direction", "Status"],
                    "icon": "message",
                    "new_url": None,
                    "view_all_url": f"/messages?contact={contact_id}&related=1&back_to=/contacts/{contact_id}?tab=related",
                    "total_count": len(messages),
                    "items": [{
                        "name": message.content[:40] + ("..." if message.content and len(message.content) > 40 else "") if message.content else f"Message {message.id}",
                        "direction": message.direction or "",
                        "status": message.status or "",
                        "_href": f"/messages/{message.id}",
                    } for message in messages[:5]]
                })

            assets = AssetService.get_assets(db, contact=contact_id)
            if assets:
                related_lists.append({
                    "title": "Assets",
                    "columns": ["Name", "Vin", "Status"],
                    "icon": "asset",
                    "new_url": f"/assets/new-modal?contact={contact_id}",
                    "view_all_url": f"/assets?contact={contact_id}&related=1&back_to=/contacts/{contact_id}?tab=related",
                    "total_count": len(assets),
                    "items": [{
                        "name": a.name,
                        "vin": a.vin,
                        "status": a.status,
                        "_href": f"/assets/{a.id}",
                    } for a in assets[:5]]
                })

            return templates.TemplateResponse(request, "contact/detail_view.html", {
                "request": request, "object_type": "Contact", "plural_type": "contacts",
                "record_id": contact_id, "record_name": f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}",
                "details": details, "created_at": contact.created_at,
                "updated_at": contact.updated_at, "related_lists": related_lists
            })
        except Exception as e:
            logger.error(f"Error rendering contact detail {contact_id}: {str(e)}")
            return RedirectResponse(url="/contacts?error=Internal+server+error")

    @staticmethod
    @router.get("/", response_class=HTMLResponse)
    @handle_agent_errors
    async def list_contacts(request: Request, db: Session = Depends(get_db)):
        try:
            related_mode = request.query_params.get("related") == "1" or bool(request.query_params.get("back_to"))
            back_url = request.query_params.get("back_to") or "/contacts"
            record_id = request.query_params.get("id")
            filters = {}
            for key in ["tier"]:
                value = request.query_params.get(key)
                if value:
                    filters[key] = value
                    related_mode = True
            related_mode = related_mode or bool(record_id)
            if record_id:
                filters["id"] = record_id
            
            contacts = db.query(Contact).filter_by(**filters).all() if filters else ContactService.get_contacts(db)
            items = []
            for c in contacts:
                items.append({
                    "id": c.id,
                    "name": f"{c.first_name if c.first_name else ''} {c.last_name if c.last_name else ''}".strip() or c.name or "",
                    "email": c.email,
                    "phone": c.phone,
                    "tier": c.tier,
                    "created": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
                    "edit_url": f"/contacts/new-modal?id={c.id}",
                    "_href": f"/contacts/{c.id}",
                })

            if related_mode:
                new_url = None
                page_icon = "contact"
                return templates.TemplateResponse(request, "related/list_view.html", {
                    "request": request,
                    "page_title": "Contacts",
                    "items": items,
                    "columns": ContactRouter.CONTACT_LIST_COLUMNS,
                    "back_url": back_url,
                    "new_url": new_url,
                    "page_icon": page_icon,
                    "show_actions": True,
                })

            saved_views = LeadListViewService.list_views(
                db,
                ContactRouter.CONTACT_LIST_COLUMNS,
                object_type="Contact",
                builtin_views=ContactRouter.CONTACT_LIST_BUILTINS,
            )
            saved_view_ids = {view["id"] for view in saved_views}
            pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
            requested_view = request.query_params.get("view")
            current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "contact-all")

            return templates.TemplateResponse(request, "contact/list_view.html", {
                "request": request,
                "object_type": "Contact",
                "plural_type": "contacts",
                "items": items,
                "columns": ContactRouter.CONTACT_LIST_COLUMNS,
                "current_view": current_view,
                "list_view_options": [
                    {"value": view["id"], "label": view["label"]}
                    for view in saved_views
                ],
                "saved_views": saved_views,
                "pinned_view_id": pinned_view_id,
                "list_view_storage_key": "d4_recent_contacts",
            })
        except Exception as e:
            logger.error(f"Error listing contacts: {str(e)}")
            return HTMLResponse(content="Internal Server Error", status_code=500)

    @staticmethod
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
        try:
            contact = ContactService.create_contact(
                db, first_name=first_name, last_name=last_name, gender=gender,
                email=email, phone=phone, website=website,
                tier=tier, description=description
            )
            return RedirectResponse(url=f"/contacts/{contact.id}?success=Record+created+successfully", status_code=303)
        except Exception as e:
            logger.error(f"Error creating contact: {str(e)}")
            return RedirectResponse(url="/contacts?error=Failed+to+create+record", status_code=303)

    @staticmethod
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
        try:
            ContactService.update_contact(
                db, contact_id, first_name=first_name, last_name=last_name, 
                gender=gender, email=email, phone=phone,
                website=website, tier=tier, description=description
            )
            return RedirectResponse(url=f"/contacts/{contact_id}" + "?success=Record+updated+successfully", status_code=303)
        except Exception as e:
            logger.error(f"Error updating contact {contact_id}: {str(e)}")
            return RedirectResponse(url=f"/contacts/{contact_id}?error=Failed+to+update+record", status_code=303)

    @staticmethod
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
        return await ContactRouter.update_contact(request, contact_id, first_name, last_name, gender, email, phone, website, tier, description, db)

    @staticmethod
    @router.post("/{contact_id}/batch-save")
    @handle_agent_errors
    async def batch_save_contact(contact_id: str, updates: dict, db: Session = Depends(get_db)):
        try:
            """Handles JSON batch updates from inline editing."""
            clean_updates = {}
            for k, v in updates.items():
                key = k.lower().replace(" ", "_")
                if key == "full_name":
                    parts = str(v).split(" ", 1)
                    clean_updates["first_name"] = parts[0]
                    clean_updates["last_name"] = parts[1] if len(parts) > 1 else ""
                else:
                    clean_updates[key] = v
            
            ContactService.update_contact(db, contact_id, **clean_updates)
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error batch saving contact {contact_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

    @staticmethod
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

    @staticmethod
    @router.post("/{contact_id}/restore")
    async def restore_contact_endpoint(contact_id: str, db: Session = Depends(get_db)):
        try:
            success = ContactService.restore_contact(db, contact_id)
            if success:
                return {"status": "success"}
            return {"status": "error", "message": "Contact not found"}
        except Exception as e:
            logger.error(f"Restore Contact error: {e}")
            return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
