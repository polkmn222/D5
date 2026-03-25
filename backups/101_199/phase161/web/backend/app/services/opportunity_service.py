from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from db.models import Asset, Model, Opportunity, Product, Lead
from web.backend.app.utils.timezone import get_kst_now_naive, make_naive_kst
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class OpportunityService:
    @staticmethod
    def _get_active_asset(db: Session, asset_id: Optional[str]) -> Optional[Asset]:
        try:
            if not asset_id: return None
            return db.query(Asset).filter(Asset.id == asset_id, Asset.deleted_at == None).first()
        except Exception as e:
            logger.error(f"Error fetching active asset {asset_id}: {str(e)}")
            return None

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
    def _normalize_lookup_dependencies(db: Session, current: Optional[Opportunity], kwargs: dict) -> dict:
        try:
            normalized = dict(kwargs)
            force_null_fields = set(normalized.pop("_force_null_fields", []) or [])
            
            # Logic to sync Brand/Model based on Product
            if "product" in normalized:
                product_id = normalized.get("product")
                if product_id:
                    product = OpportunityService._get_active_product(db, product_id)
                    if product:
                        normalized["model"] = product.model
                        if product.model:
                            model = OpportunityService._get_active_model(db, product.model)
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
    def create_opportunity(db: Session, **kwargs) -> Optional[Opportunity]:
        clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
        
        # Apply normalization
        normalized_kwargs = OpportunityService._normalize_lookup_dependencies(db, None, clean_kwargs)
        
        opp = Opportunity(id=get_id("Opportunity"), created_at=get_kst_now_naive(), updated_at=get_kst_now_naive(), **normalized_kwargs)
        db.add(opp)
        db.commit()
        db.refresh(opp)
        return opp

    @staticmethod
    @handle_agent_errors
    def get_opportunities(db: Session) -> List[Opportunity]:
        return db.query(Opportunity).filter(Opportunity.deleted_at == None).all()

    @staticmethod
    @handle_agent_errors
    def get_opportunity(db: Session, opp_id: str) -> Optional[Opportunity]:
        return db.query(Opportunity).filter(Opportunity.id == opp_id, Opportunity.deleted_at == None).first()

    @staticmethod
    @handle_agent_errors
    def update_opportunity(db: Session, opp_id: str, **kwargs) -> Optional[Opportunity]:
        opp = OpportunityService.get_opportunity(db, opp_id)
        if not opp: return None
        
        # Apply normalization
        normalized_kwargs = OpportunityService._normalize_lookup_dependencies(db, opp, kwargs)
        force_null_fields = normalized_kwargs.pop("_force_null_fields", [])

        for key, value in normalized_kwargs.items():
            if hasattr(opp, key): setattr(opp, key, value)
        
        for field in force_null_fields:
            if hasattr(opp, field): setattr(opp, field, None)

        opp.updated_at = get_kst_now_naive()
        db.commit()
        db.refresh(opp)
        return opp

    @staticmethod
    @handle_agent_errors
    def delete_opportunity(db: Session, opp_id: str, hard_delete: bool = False) -> bool:
        opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        if not opp: return False
        if hard_delete:
            db.query(Lead).filter(Lead.converted_opportunity == opp_id).update({Lead.converted_opportunity: None}, synchronize_session=False)
            db.delete(opp)
        else: opp.deleted_at = get_kst_now_naive()
        db.commit()
        return True

    @staticmethod
    @handle_agent_errors
    def update_last_viewed(db: Session, opp_id: str) -> Optional[Opportunity]:
        return OpportunityService.update_opportunity(db, opp_id, last_viewed_at=get_kst_now_naive())

    @staticmethod
    @handle_agent_errors
    def get_by_contact(db: Session, contact: str) -> List[Opportunity]:
        return db.query(Opportunity).filter(Opportunity.contact == contact, Opportunity.deleted_at == None).all()

    @staticmethod
    @handle_agent_errors
    def get_recent_clicked(db: Session, limit: int = 5) -> List[Opportunity]:
        return db.query(Opportunity).filter(
            Opportunity.deleted_at == None,
            Opportunity.last_viewed_at != None
        ).order_by(Opportunity.last_viewed_at.desc()).limit(limit).all()

    @staticmethod
    @handle_agent_errors
    def get_performance_stats(db: Session, horizon_days: int = 7) -> dict:
        try:
            horizon = get_kst_now_naive() - timedelta(days=horizon_days)
            opps = db.query(Opportunity).filter(
                Opportunity.deleted_at == None,
                Opportunity.created_at >= horizon
            ).all()
            stages = ["Qualification", "Test Drive", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"]
            performance_by_stage = []
            for stage in stages:
                amount = sum(o.amount for o in opps if o.stage == stage and o.amount)
                performance_by_stage.append({"label": stage, "amount": int(amount)})
            closed_won_amount = sum(o.amount for o in opps if o.stage == 'Closed Won' and o.amount)
            return {
                "by_stage": performance_by_stage,
                "closed_won": f"{int(closed_won_amount):,}",
                "total_target": 1000000000
            }
        except Exception as e:
            logger.error(f"Error calculating performance stats: {str(e)}")
            return {"by_stage": [], "closed_won": "0", "total_target": 1000000000}
