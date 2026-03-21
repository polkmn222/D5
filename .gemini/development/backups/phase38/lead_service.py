from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Lead, Opportunity, Contact
from backend.app.utils.sf_id import get_id
from backend.app.utils.timezone import get_kst_now_naive
from .base_service import BaseService
from backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class LeadService(BaseService[Lead]):
    model = Lead
    object_name = "Lead"

    @classmethod
    @handle_agent_errors
    def create_lead(cls, db: Session, **kwargs) -> Lead:
        try:
            return cls.create(db, **kwargs)
        except Exception as e:
            logger.error(f"Failed to create lead: {str(e)}")
            raise e

    @classmethod
    @handle_agent_errors
    def get_leads(cls, db: Session, converted: bool = False) -> List[Lead]:
        try:
            # BaseService.list handles exceptions by returning [], so no need for explicit try-except here.
            return cls.list(db, is_converted=converted)
        except Exception as e:
            logger.error(f"Failed to get leads: {str(e)}")
            return []

    @classmethod
    @handle_agent_errors
    def get_lead(cls, db: Session, lead_id: str) -> Optional[Lead]:
        try:
            return cls.get(db, lead_id)
        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {str(e)}")
            return None

    @classmethod
    @handle_agent_errors
    def update_lead(cls, db: Session, lead_id: str, **kwargs) -> Optional[Lead]:
        try:
            return cls.update(db, lead_id, **kwargs)
        except Exception as e:
            logger.error(f"Failed to update lead {lead_id}: {str(e)}")
            raise e

    @classmethod
    @handle_agent_errors
    def delete_lead(cls, db: Session, lead_id: str) -> bool:
        try:
            return cls.delete(db, lead_id)
        except Exception as e:
            logger.error(f"Failed to delete lead {lead_id}: {str(e)}")
            return False

    @classmethod
    @handle_agent_errors
    def restore_lead(cls, db: Session, lead_id: str) -> bool:
        try:
            return cls.restore(db, lead_id)
        except Exception as e:
            logger.error(f"Failed to restore lead {lead_id}: {str(e)}")
            return False

    @classmethod
    @handle_agent_errors
    def update_stage(cls, db: Session, lead_id: str, stage: str) -> Optional[Lead]:
        try:
            return cls.update_lead(db, lead_id, status=stage)
        except Exception as e:
            logger.error(f"Failed to update stage for lead {lead_id}: {str(e)}")
            raise e

    @classmethod
    @handle_agent_errors
    def toggle_follow(cls, db: Session, lead_id: str, enabled: bool) -> Optional[Lead]:
        try:
            return cls.update_lead(db, lead_id, is_followed=enabled)
        except Exception as e:
            logger.error(f"Failed to toggle follow for lead {lead_id}: {str(e)}")
            raise e

    @staticmethod
    def _create_converted_contact(db: Session, lead: Lead, name: str = None) -> Contact:
        try:
            final_name = name if name else f"{lead.first_name if lead.first_name else ''} {lead.last_name if lead.last_name else ''}".strip() or "New Contact"
            contact = Contact(
                id=get_id("Contact"),
                first_name=lead.first_name,
                last_name=lead.last_name,
                name=final_name,
                email=lead.email,
                phone=lead.phone,
                gender=lead.gender,
                description=lead.description,
                created_at=get_kst_now_naive(),
                updated_at=get_kst_now_naive()
            )
            db.add(contact)
            db.flush()
            return contact
        except Exception as e:
            logger.error(f"Failed to create converted contact for lead {lead.id}: {str(e)}")
            raise e

    @staticmethod
    def _create_converted_opportunity(db: Session, lead: Lead, contact_id: str, opp_name: str) -> Opportunity:
        try:
            final_name = opp_name if opp_name else f"{lead.last_name if lead.last_name else 'Lead'} - Deal"
            opportunity = Opportunity(
                id=get_id("Opportunity"),
                contact=contact_id,
                lead=lead.id,
                brand=lead.brand,
                model=lead.model,
                product=lead.product,
                name=final_name,
                amount=0,
                stage="Qualification",
                status="Open",
                created_at=get_kst_now_naive(),
                updated_at=get_kst_now_naive()
            )
            db.add(opportunity)
            db.flush()
            return opportunity
        except Exception as e:
            logger.error(f"Failed to create converted opportunity for lead {lead.id}: {str(e)}")
            raise e

    @classmethod
    def convert_lead(cls, db: Session, lead_id: str) -> Optional[dict]:
        """Simple wrapper for backward compatibility with tests."""
        try:
            return cls.convert_lead_advanced(db, lead_id)
        except Exception as e:
            logger.error(f"Failed to convert lead {lead_id}: {str(e)}")
            raise e

    @classmethod
    @handle_agent_errors
    def convert_lead_advanced(
        cls, db: Session, lead_id: str,
        name: str = None,
        opportunity_name: str = None,
        dont_create_opp: bool = False,
        converted_status: str = "Qualified"
    ) -> Optional[dict]:
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at == None).first()
            if not lead or lead.is_converted:
                return None

            contact = cls._create_converted_contact(db, lead, name)
            
            opportunity = None
            if not dont_create_opp:
                opportunity = cls._create_converted_opportunity(db, lead, contact.id, opportunity_name)

            lead.is_converted = True
            lead.converted_contact = contact.id
            lead.converted_opportunity = opportunity.id if opportunity else None
            lead.status = converted_status
            lead.updated_at = get_kst_now_naive()
            
            db.commit()
            return {"contact": contact, "opportunity": opportunity}
        except Exception as e:
            db.rollback()
            logger.error(f"Lead conversion failed: {str(e)}")
            raise e
