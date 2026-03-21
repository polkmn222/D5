from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.app.services.surem_service import SureMService
import logging
from db.database import get_db
from sqlalchemy.orm import Session
from backend.app.utils.error_handler import handle_agent_errors

router = APIRouter(prefix="/api/test", tags=["SureM Debug"])
logger = logging.getLogger(__name__)

class SmsRequest(BaseModel):
    text: str

class MmsRequest(BaseModel):
    subject: str
    text: str
    image_key: Optional[str] = None

@router.post("/sms")
@handle_agent_errors
async def test_send_sms(req: SmsRequest, db: Session = Depends(get_db)):
    try:
        result = SureMService.send_sms(db, req.text)
        if result.get("status") == "success":
            return result
        else:
            return JSONResponse(status_code=400, content=result)
    except Exception as e:
        logger.error(f"Error testing SMS: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.post("/upload-image")
async def test_upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        if file.content_type not in ["image/jpeg", "image/jpg"]:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Only JPG/JPEG files are allowed."})
            
        content = await file.read()
        if len(content) > 500 * 1024:
            return JSONResponse(status_code=400, content={"status": "error", "message": "File size exceeds 500KB limit."})
            
        result = SureMService.upload_image(db, content, file.filename)
        if result.get("status") == "success":
            return result
        else:
            return JSONResponse(status_code=400, content=result)
    except Exception as e:
        logger.error(f"Error testing image upload: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.post("/mms")
async def test_send_mms(req: MmsRequest, db: Session = Depends(get_db)):
    try:
        result = SureMService.send_mms(db, req.subject, req.text, req.image_key)
        if result.get("status") == "success":
            return result
        else:
            return JSONResponse(status_code=400, content=result)
    except Exception as e:
        logger.error(f"Error testing MMS: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
