from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Contact
from .base_service import BaseService
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class ContactService(BaseService[Contact]):
    model = Contact
    object_name = "Contact"

    @classmethod
    @handle_agent_errors
    def create_contact(cls, db: Session, **kwargs) -> Contact:
        try:
            return cls.create(db, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in create_contact: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def get_contacts(cls, db: Session) -> List[Contact]:
        try:
            return cls.list(db)
        except Exception as e:
            logger.error(f"Error in get_contacts: {e}")
            return []

    @classmethod
    @handle_agent_errors
    def get_contact(cls, db: Session, contact_id: str) -> Optional[Contact]:
        try:
            return cls.get(db, contact_id)
        except Exception as e:
            logger.error(f"Error in get_contact: {e}")
            return None

    @classmethod
    @handle_agent_errors
    def update_contact(cls, db: Session, contact_id: str, **kwargs) -> Optional[Contact]:
        try:
            return cls.update(db, contact_id, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in update_contact: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def delete_contact(cls, db: Session, contact_id: str) -> bool:
        try:
            return cls.delete(db, contact_id)
        except Exception as e:
            logger.error(f"Critical error in delete_contact: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def restore_contact(cls, db: Session, contact_id: str) -> bool:
        try:
            return cls.restore(db, contact_id)
        except Exception as e:
            logger.error(f"Critical error in restore_contact: {e}")
            raise e
