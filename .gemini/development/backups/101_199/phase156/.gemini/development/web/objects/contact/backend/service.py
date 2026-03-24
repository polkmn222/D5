from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Contact, MessageSend, Opportunity, Asset, Lead
from web.core.backend.utils.sf_id import get_id
from web.core.backend.utils.timezone import get_kst_now_naive
from web.core.backend.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class ContactService:
    """
    ContactService handles all business logic for the Contact object.
    All methods are static and wrapped in try-except blocks.
    """

    @staticmethod
    @handle_agent_errors
    def create_contact(db: Session, **kwargs) -> Optional[Contact]:
        try:
            clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
            contact = Contact(
                id=get_id("Contact"),
                created_at=get_kst_now_naive(),
                updated_at=get_kst_now_naive(),
                **clean_kwargs
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)
            return contact
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create contact: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def get_contacts(db: Session) -> List[Contact]:
        try:
            return db.query(Contact).filter(Contact.deleted_at == None).all()
        except Exception as e:
            logger.error(f"Failed to list contacts: {str(e)}")
            return []

    @staticmethod
    @handle_agent_errors
    def get_contact(db: Session, contact_id: str) -> Optional[Contact]:
        try:
            return db.query(Contact).filter(
                Contact.id == contact_id,
                Contact.deleted_at == None
            ).first()
        except Exception as e:
            logger.error(f"Failed to get contact {contact_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def update_contact(db: Session, contact_id: str, **kwargs) -> Optional[Contact]:
        try:
            contact = ContactService.get_contact(db, contact_id)
            if not contact:
                return None
            force_null_fields = kwargs.pop("_force_null_fields", []) or []
            for key, value in kwargs.items():
                if hasattr(contact, key):
                    setattr(contact, key, value)
            for field in force_null_fields:
                if hasattr(contact, field):
                    setattr(contact, field, None)
            contact.updated_at = get_kst_now_naive()
            db.commit()
            db.refresh(contact)
            return contact
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update contact {contact_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def delete_contact(db: Session, contact_id: str, hard_delete: bool = False) -> bool:
        try:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                return False
            
            if hard_delete:
                # Hard delete cascading logic from RecordDeleteService
                db.query(MessageSend).filter(MessageSend.contact == contact_id).delete(synchronize_session=False)
                
                # Delete Opportunities and handle Lead refs
                opp_ids = [row.id for row in db.query(Opportunity.id).filter(Opportunity.contact == contact_id).all()]
                if opp_ids:
                    db.query(Lead).filter(Lead.converted_opportunity.in_(opp_ids)).update({Lead.converted_opportunity: None}, synchronize_session=False)
                    db.query(Opportunity).filter(Opportunity.id.in_(opp_ids)).delete(synchronize_session=False)
                
                # Delete Assets and handle Opportunity refs
                asset_ids = [row.id for row in db.query(Asset.id).filter(Asset.contact == contact_id).all()]
                if asset_ids:
                    db.query(Opportunity).filter(Opportunity.asset.in_(asset_ids)).delete(synchronize_session=False)
                    db.query(Asset).filter(Asset.id.in_(asset_ids)).delete(synchronize_session=False)
                
                db.query(Lead).filter(Lead.converted_contact == contact_id).update({Lead.converted_contact: None}, synchronize_session=False)
                db.delete(contact)
            else:
                contact.deleted_at = get_kst_now_naive()
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete contact {contact_id}: {str(e)}")
            return False

    @staticmethod
    @handle_agent_errors
    def restore_contact(db: Session, contact_id: str) -> bool:
        try:
            contact = db.query(Contact).filter(Contact.id == contact_id).first()
            if not contact:
                return False
            contact.deleted_at = None
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to restore contact {contact_id}: {str(e)}")
            return False
