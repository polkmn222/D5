from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from db.database import get_db
from web.backend.app.services.trash_service import TrashService
from web.backend.app.core.templates import templates
from web.backend.app.utils.error_handler import handle_agent_errors
import logging

router = APIRouter(prefix="/trash", tags=["Recycle Bin"])
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
@handle_agent_errors
async def trash_list_view(request: Request, db: Session = Depends(get_db)):
    try:
        items = TrashService.list_deleted_records(db)
        return templates.TemplateResponse(request, "trash/list_view.html", {
            "request": request,
            "items": items,
            "page_title": "Recycle Bin"
        })
    except Exception as e:
        logger.error(f"Error loading trash list: {e}")
        return RedirectResponse(url="/?error=Error+loading+Recycle+Bin")

@router.post("/restore")
@handle_agent_errors
async def restore_record_endpoint(
    object_type: str = Form(...),
    record_id: str = Form(...),
    db: Session = Depends(get_db)
):
    success = TrashService.restore_record(db, object_type, record_id)
    if success:
        return RedirectResponse(url="/trash?success=Record+restored+successfully", status_code=303)
    return RedirectResponse(url="/trash?error=Failed+to+restore+record", status_code=303)

@router.post("/hard-delete")
@handle_agent_errors
async def hard_delete_record_endpoint(
    object_type: str = Form(...),
    record_id: str = Form(...),
    db: Session = Depends(get_db)
):
    success = TrashService.hard_delete_record(db, object_type, record_id)
    if success:
        return RedirectResponse(url="/trash?success=Record+deleted+permanently", status_code=303)
    return RedirectResponse(url="/trash?error=Failed+to+delete+record", status_code=303)
