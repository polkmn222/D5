from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Contact, Lead, Model, Opportunity, Product
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.timezone import get_kst_now_naive
from web.backend.app.utils.error_handler import handle_agent_errors
from web.backend.app.core.enums import LeadStatus

logger = logging.getLogger(__name__)

class LeadService:
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
            
            if force_null_fields:
                normalized["_force_null_fields"] = sorted(force_null_fields)
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing lookup dependencies: {str(e)}")
            return kwargs

    @staticmethod
    @handle_agent_errors
    def create_lead(db: Session, **kwargs) -> Optional[Lead]:
        clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
        
        # Apply normalization before create
        normalized_kwargs = LeadService._normalize_lookup_dependencies(db, None, clean_kwargs)
        
        lead = Lead(id=get_id("Lead"), created_at=get_kst_now_naive(), updated_at=get_kst_now_naive(), **normalized_kwargs)
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    @staticmethod
    @handle_agent_errors
    def get_leads(db: Session, converted: bool = False) -> List[Lead]:
        return db.query(Lead).filter(Lead.is_converted == converted, Lead.deleted_at == None).all()

    @staticmethod
    @handle_agent_errors
    def get_lead(db: Session, lead_id: str) -> Optional[Lead]:
        return db.query(Lead).filter(Lead.id == lead_id, Lead.deleted_at == None).first()

    @staticmethod
    @handle_agent_errors
    def update_lead(db: Session, lead_id: str, **kwargs) -> Optional[Lead]:
        lead = LeadService.get_lead(db, lead_id)
        if not lead: return None
        
        # Apply normalization before update
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

    @staticmethod
    @handle_agent_errors
    def delete_lead(db: Session, lead_id: str, hard_delete: bool = False) -> bool:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead: return False
        if hard_delete: db.delete(lead)
        else: lead.deleted_at = get_kst_now_naive()
        db.commit()
        return True

    @staticmethod
    @handle_agent_errors
    def restore_lead(db: Session, lead_id: str) -> bool:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead: return False
        lead.deleted_at = None
        db.commit()
        return True

    @staticmethod
    @handle_agent_errors
    def toggle_follow(db: Session, lead_id: str, enabled: bool) -> Optional[Lead]:
        return LeadService.update_lead(db, lead_id, is_followed=enabled)

    @staticmethod
    @handle_agent_errors
    def update_stage(db: Session, lead_id: str, stage: str) -> Optional[Lead]:
        return LeadService.update_lead(db, lead_id, status=stage)

    @staticmethod
    @handle_agent_errors
    def convert_lead_advanced(db: Session, lead_id: str, name: str = None, opportunity_name: str = None, dont_create_opp: bool = False, converted_status: str = "Qualified") -> Optional[dict]:
        try:
            lead = LeadService.get_lead(db, lead_id)
            if not lead or lead.is_converted: return None
            
            final_name = name if name else f"{lead.first_name if lead.first_name else ''} {lead.last_name if lead.last_name else ''}".strip() or "New Contact"
            contact = Contact(
                id=get_id("Contact"),
                first_name=lead.first_name, last_name=lead.last_name, name=final_name,
                email=lead.email, phone=lead.phone, gender=lead.gender, description=lead.description,
                created_at=get_kst_now_naive(), updated_at=get_kst_now_naive()
            )
            db.add(contact)
            db.flush()
            
            opportunity = None
            if not dont_create_opp:
                opp_final_name = opportunity_name if opportunity_name else f"{lead.last_name if lead.last_name else 'Lead'} - Deal"
                opportunity = Opportunity(
                    id=get_id("Opportunity"),
                    contact=contact.id, lead=lead.id, brand=lead.brand, model=lead.model, product=lead.product,
                    name=opp_final_name, amount=0, stage="Qualification", status="Open",
                    created_at=get_kst_now_naive(), updated_at=get_kst_now_naive()
                )
                db.add(opportunity)
                db.flush()
            
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
