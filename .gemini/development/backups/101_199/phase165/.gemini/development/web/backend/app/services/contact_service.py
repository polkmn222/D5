from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Contact
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.timezone import get_kst_now_naive
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class ContactService:
    @staticmethod
    @handle_agent_errors
    def create_contact(db: Session, **kwargs) -> Optional[Contact]:
        clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
        contact = Contact(id=get_id("Contact"), created_at=get_kst_now_naive(), updated_at=get_kst_now_naive(), **clean_kwargs)
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact

    @staticmethod
    @handle_agent_errors
    def get_contacts(db: Session) -> List[Contact]:
        return db.query(Contact).filter(Contact.deleted_at == None).all()

    @staticmethod
    @handle_agent_errors
    def get_contact(db: Session, contact_id: str) -> Optional[Contact]:
        return db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at == None).first()

    @staticmethod
    @handle_agent_errors
    def update_contact(db: Session, contact_id: str, **kwargs) -> Optional[Contact]:
        contact = ContactService.get_contact(db, contact_id)
        if not contact: return None
        for key, value in kwargs.items():
            if hasattr(contact, key): setattr(contact, key, value)
        contact.updated_at = get_kst_now_naive()
        db.commit()
        db.refresh(contact)
        return contact

    @staticmethod
    @handle_agent_errors
    def delete_contact(db: Session, contact_id: str, hard_delete: bool = False) -> bool:
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact: return False
        if hard_delete: db.delete(contact)
        else: contact.deleted_at = get_kst_now_naive()
        db.commit()
        return True
