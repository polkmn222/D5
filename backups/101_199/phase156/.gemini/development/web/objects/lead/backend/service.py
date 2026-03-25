from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Contact, Lead, Model, Opportunity, Product
from web.core.backend.utils.sf_id import get_id
from web.core.backend.utils.timezone import get_kst_now_naive
from web.core.backend.utils.error_handler import handle_agent_errors
from web.core.backend.core.enums import LeadStatus

logger = logging.getLogger(__name__)

class LeadService:
    """
    LeadService handles all business logic for the Lead object.
    All methods are static and wrapped in try-except blocks.
    """

    @staticmethod
    def _get_active_model(db: Session, model_id: Optional[str]) -> Optional[Model]:
        try:
            if not model_id: return None
            return db.query(Model).filter(Model.id == model_id, Model.deleted_at == None).first()
        except Exception as e:
            logger.error(f"Error fetching active model {model_id}: {str(e)}")
            return None

    @staticmethod
    def _get_active_product(db: Session, product_id: Optional[str]) -> Optional[Product]:
        try:
            if not product_id: return None
            return db.query(Product).filter(Product.id == product_id, Product.deleted_at == None).first()
        except Exception as e:
            logger.error(f"Error fetching active product {product_id}: {str(e)}")
            return None

    @staticmethod
    def _normalize_lookup_dependencies(db: Session, current: Optional[Lead], kwargs: dict) -> dict:
        try:
            normalized = dict(kwargs)
            force_null_fields = set(normalized.pop("_force_null_fields", []) or [])
            if "product" in normalized:
                product_id = normalized.get("product")
                if product_id:
                    product = LeadService._get_active_product(db, product_id)
                    if product:
                        normalized["model"] = product.model
                        if product.model:
                            model = LeadService._get_active_model(db, product.model)
                            normalized["brand"] = model.brand if model and model.brand else product.brand
                        else:
                            normalized["brand"] = product.brand
                else:
                    normalized["product"] = None
                    force_null_fields.add("product")
            if "model" in normalized:
                model_id = normalized.get("model")
                if model_id:
                    model = LeadService._get_active_model(db, model_id)
                    if model:
                        normalized["brand"] = model.brand
                        product_id = normalized.get("product", current.product if current else None)
                        if product_id:
                            product = LeadService._get_active_product(db, product_id)
                            if not product or product.model != model.id:
                                normalized["product"] = None
                                force_null_fields.add("product")
                else:
                    normalized["model"] = None
                    force_null_fields.add("model")
                    normalized["product"] = None
                    force_null_fields.add("product")
            if "brand" in normalized:
                brand_id = normalized.get("brand")
                if brand_id:
                    model_id = normalized.get("model", current.model if current else None)
                    if model_id:
                        model = LeadService._get_active_model(db, model_id)
                        if not model or model.brand != brand_id:
                            normalized["model"] = None
                            force_null_fields.add("model")
                            normalized["product"] = None
                            force_null_fields.add("product")
                    product_id = normalized.get("product", current.product if current else None)
                    if product_id:
                        product = LeadService._get_active_product(db, product_id)
                        if not product or product.brand != brand_id:
                            normalized["product"] = None
                            force_null_fields.add("product")
                else:
                    normalized["brand"] = None
                    force_null_fields.add("brand")
                    normalized["model"] = None
                    force_null_fields.add("model")
                    normalized["product"] = None
                    force_null_fields.add("product")
            if force_null_fields:
                normalized["_force_null_fields"] = sorted(force_null_fields)
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing lookup dependencies: {str(e)}")
            return kwargs

    @staticmethod
    @handle_agent_errors
    def create_lead(db: Session, **kwargs) -> Optional[Lead]:
        try:
            clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
            lead = Lead(
                id=get_id("Lead"),
                created_at=get_kst_now_naive(),
                updated_at=get_kst_now_naive(),
                **clean_kwargs
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            return lead
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create lead: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def get_leads(db: Session, converted: bool = False) -> List[Lead]:
        try:
            return db.query(Lead).filter(
                Lead.is_converted == converted,
                Lead.deleted_at == None
            ).all()
        except Exception as e:
            logger.error(f"Failed to get leads: {str(e)}")
            return []

    @staticmethod
    @handle_agent_errors
    def get_lead(db: Session, lead_id: str) -> Optional[Lead]:
        try:
            return db.query(Lead).filter(
                Lead.id == lead_id,
                Lead.deleted_at == None
            ).first()
        except Exception as e:
            logger.error(f"Failed to get lead {lead_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def update_lead(db: Session, lead_id: str, **kwargs) -> Optional[Lead]:
        try:
            lead = LeadService.get_lead(db, lead_id)
            if not lead: return None
            normalized_kwargs = LeadService._normalize_lookup_dependencies(db, lead, kwargs)
            force_null_fields = normalized_kwargs.pop("_force_null_fields", [])
            for key, value in normalized_kwargs.items():
                if hasattr(lead, key): setattr(lead, key, value)
            for field in force_null_fields:
                if hasattr(lead, field): setattr(lead, field, None)
            lead.updated_at = get_kst_now_naive()
            db.commit()
            db.refresh(lead)
            return lead
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update lead {lead_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def delete_lead(db: Session, lead_id: str, hard_delete: bool = False) -> bool:
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead: return False
            if hard_delete:
                db.query(Opportunity).filter(Opportunity.lead == lead_id).delete(synchronize_session=False)
                db.delete(lead)
            else:
                lead.deleted_at = get_kst_now_naive()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete lead {lead_id}: {str(e)}")
            return False

    @staticmethod
    @handle_agent_errors
    def restore_lead(db: Session, lead_id: str) -> bool:
        try:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead: return False
            lead.deleted_at = None
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to restore lead {lead_id}: {str(e)}")
            return False

    @staticmethod
    @handle_agent_errors
    def update_stage(db: Session, lead_id: str, stage: str) -> Optional[Lead]:
        try:
            return LeadService.update_lead(db, lead_id, status=stage)
        except Exception as e:
            logger.error(f"Failed to update stage for lead {lead_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def toggle_follow(db: Session, lead_id: str, enabled: bool) -> Optional[Lead]:
        try:
            return LeadService.update_lead(db, lead_id, is_followed=enabled)
        except Exception as e:
            logger.error(f"Failed to toggle follow for lead {lead_id}: {str(e)}")
            return None

    @staticmethod
    def _create_converted_contact(db: Session, lead: Lead, name: str = None) -> Optional[Contact]:
        try:
            final_name = name if name else f"{lead.first_name if lead.first_name else ''} {lead.last_name if lead.last_name else ''}".strip() or "New Contact"
            contact = Contact(
                id=get_id("Contact"),
                first_name=lead.first_name, last_name=lead.last_name, name=final_name,
                email=lead.email, phone=lead.phone, gender=lead.gender, description=lead.description,
                created_at=get_kst_now_naive(), updated_at=get_kst_now_naive()
            )
            db.add(contact)
            db.flush()
            return contact
        except Exception as e:
            logger.error(f"Failed to create converted contact for lead {lead.id}: {str(e)}")
            return None

    @staticmethod
    def _create_converted_opportunity(db: Session, lead: Lead, contact_id: str, opp_name: str) -> Optional[Opportunity]:
        try:
            final_name = opp_name if opp_name else f"{lead.last_name if lead.last_name else 'Lead'} - Deal"
            opportunity = Opportunity(
                id=get_id("Opportunity"),
                contact=contact_id, lead=lead.id, brand=lead.brand, model=lead.model, product=lead.product,
                name=final_name, amount=0, stage="Qualification", status="Open",
                created_at=get_kst_now_naive(), updated_at=get_kst_now_naive()
            )
            db.add(opportunity)
            db.flush()
            return opportunity
        except Exception as e:
            logger.error(f"Failed to create converted opportunity for lead {lead.id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def convert_lead_advanced(db: Session, lead_id: str, name: str = None, opportunity_name: str = None, dont_create_opp: bool = False, converted_status: str = "Qualified") -> Optional[dict]:
        try:
            lead = LeadService.get_lead(db, lead_id)
            if not lead or lead.is_converted: return None
            contact = LeadService._create_converted_contact(db, lead, name)
            if not contact: return None
            opportunity = None
            if not dont_create_opp:
                opportunity = LeadService._create_converted_opportunity(db, lead, contact.id, opportunity_name)
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
            return None
