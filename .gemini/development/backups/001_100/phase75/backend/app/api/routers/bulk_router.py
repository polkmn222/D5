from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from db.database import get_db
from backend.app.utils.error_handler import handle_agent_errors
import logging
from db.models import Contact, Lead, Opportunity, VehicleSpecification, Model, Product, Asset, MessageTemplate

router = APIRouter(prefix="/bulk", tags=["Bulk Operations"])
logger = logging.getLogger(__name__)

class BulkDeleteRequest(BaseModel):
    ids: List[str]
    object_type: str

@router.post("/delete")
@handle_agent_errors
async def bulk_delete(data: BulkDeleteRequest, db: Session = Depends(get_db)):
    """
    Handles bulk soft deletion of records for supported object types.
    """
    try:
        from db.models import Contact, Lead, Opportunity, VehicleSpecification, Model, Product, Asset, MessageTemplate, MessageSend
        
        MODEL_MAP = {
            "Contact": Contact,
            "Lead": Lead,
            "Opportunity": Opportunity,
            "VehicleSpecification": VehicleSpecification,
            "Model": Model,
            "Product": Product,
            "Asset": Asset,
            "MessageTemplate": MessageTemplate,
            "MessageSend": MessageSend,
        }

        model_class = MODEL_MAP.get(data.object_type)
        
        if not model_class:
            return JSONResponse(status_code=400, content={"status": "error", "message": f"Unsupported object type: {data.object_type}"})
        
        deleted_count = 0
        from ...utils.timezone import get_kst_now_naive
        now = get_kst_now_naive()

        for record_id in data.ids:
            record = db.query(model_class).filter(model_class.id == record_id).first()
            if record and not record.deleted_at:
                record.deleted_at = now
                deleted_count += 1
        
        db.commit()
        return JSONResponse(content={"status": "success", "deleted_count": deleted_count, "message": f"deleted {deleted_count} items."})
        
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk delete error: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to delete items."})

