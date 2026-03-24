from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db.database import get_db
from ...services.contact_service import ContactService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    contacts = ContactService.get_contacts(db)
    return templates.TemplateResponse(request, "dashboard.html", {"request": request, "contacts": contacts})
