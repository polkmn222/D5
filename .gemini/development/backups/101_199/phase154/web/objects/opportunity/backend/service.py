from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from db.models import Asset, Model, Opportunity, Product, Lead
from web.core.backend.utils.timezone import get_kst_now_naive, make_naive_kst
from web.core.backend.utils.sf_id import get_id
from web.core.backend.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class OpportunityService:
    """
    OpportunityService handles all business logic for the Opportunity object.
    All methods are static and wrapped in try-except blocks.
    """

    @staticmethod
    def _get_active_asset(db: Session, asset_id: Optional[str]) -> Optional[Asset]:
        try:
            if not asset_id:
                return None
            return db.query(Asset).filter(Asset.id == asset_id, Asset.deleted_at == None).first()
        except Exception as e:
            logger.error(f"Error fetching active asset {asset_id}: {str(e)}")
            return None

    @staticmethod
    def _get_active_model(db: Session, model_id: Optional[str]) -> Optional[Model]:
        try:
            if not model_id:
                return None
            return db.query(Model).filter(Model.id == model_id, Model.deleted_at == None).first()
        except Exception as e:
            logger.error(f"Error fetching active model {model_id}: {str(e)}")
            return None

    @staticmethod
    def _get_active_product(db: Session, product_id: Optional[str]) -> Optional[Product]:
        try:
            if not product_id:
                return None
            return db.query(Product).filter(Product.id == product_id, Product.deleted_at == None).first()
        except Exception as e:
            logger.error(f"Error fetching active product {product_id}: {str(e)}")
            return None

    @staticmethod
    def _normalize_lookup_dependencies(db: Session, current: Optional[Opportunity], kwargs: dict) -> dict:
        try:
            normalized = dict(kwargs)
            force_null_fields = set(normalized.pop("_force_null_fields", []) or [])
            if "asset" in normalized:
                asset_id = normalized.get("asset")
                if asset_id:
                    asset = OpportunityService._get_active_asset(db, asset_id)
                    if asset:
                        if asset.price: normalized["amount"] = asset.price
                        normalized["product"] = asset.product
                        normalized["model"] = asset.model
                        normalized["brand"] = asset.brand
                else:
                    normalized["asset"] = None
                    force_null_fields.add("asset")
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
                        asset_id = normalized.get("asset", current.asset if current else None)
                        if asset_id:
                            asset = OpportunityService._get_active_asset(db, asset_id)
                            if not asset or asset.product != product.id:
                                normalized["asset"] = None
                                force_null_fields.add("asset")
                else:
                    normalized["product"] = None
                    force_null_fields.add("product")
                    if normalized.get("asset"):
                        normalized["asset"] = None
                        force_null_fields.add("asset")
            if "model" in normalized:
                model_id = normalized.get("model")
                if model_id:
                    model = OpportunityService._get_active_model(db, model_id)
                    if model:
                        normalized["brand"] = model.brand
                        product_id = normalized.get("product", current.product if current else None)
                        if product_id:
                            product = OpportunityService._get_active_product(db, product_id)
                            if not product or product.model != model.id:
                                normalized["product"] = None
                                force_null_fields.add("product")
                        asset_id = normalized.get("asset", current.asset if current else None)
                        if asset_id:
                            asset = OpportunityService._get_active_asset(db, asset_id)
                            if not asset or asset.model != model.id:
                                normalized["asset"] = None
                                force_null_fields.add("asset")
                else:
                    normalized["model"] = None
                    force_null_fields.add("model")
                    normalized["product"] = None
                    force_null_fields.add("product")
                    normalized["asset"] = None
                    force_null_fields.add("asset")
            if "brand" in normalized:
                brand_id = normalized.get("brand")
                if brand_id:
                    model_id = normalized.get("model", current.model if current else None)
                    if model_id:
                        model = OpportunityService._get_active_model(db, model_id)
                        if not model or model.brand != brand_id:
                            normalized["model"] = None
                            force_null_fields.add("model")
                            normalized["product"] = None
                            force_null_fields.add("product")
                            normalized["asset"] = None
                            force_null_fields.add("asset")
                    product_id = normalized.get("product", current.product if current else None)
                    if product_id:
                        product = OpportunityService._get_active_product(db, product_id)
                        if not product or product.brand != brand_id:
                            normalized["product"] = None
                            force_null_fields.add("product")
                            normalized["asset"] = None
                            force_null_fields.add("asset")
                    asset_id = normalized.get("asset", current.asset if current else None)
                    if asset_id:
                        asset = OpportunityService._get_active_asset(db, asset_id)
                        if not asset or asset.brand != brand_id:
                            normalized["asset"] = None
                            force_null_fields.add("asset")
                else:
                    normalized["brand"] = None
                    force_null_fields.add("brand")
                    normalized["model"] = None
                    force_null_fields.add("model")
                    normalized["product"] = None
                    force_null_fields.add("product")
                    normalized["asset"] = None
                    force_null_fields.add("asset")
            if force_null_fields:
                normalized["_force_null_fields"] = sorted(force_null_fields)
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing lookup dependencies: {str(e)}")
            return kwargs

    @staticmethod
    @handle_agent_errors
    def create_opportunity(db: Session, **kwargs) -> Optional[Opportunity]:
        try:
            clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
            if 'stage' not in clean_kwargs: clean_kwargs['stage'] = "Prospecting"
            if 'status' not in clean_kwargs: clean_kwargs['status'] = "Open"
            if 'probability' not in clean_kwargs: clean_kwargs['probability'] = 10
            asset_id = clean_kwargs.get('asset')
            if asset_id:
                asset = OpportunityService._get_active_asset(db, asset_id)
                if asset and asset.price: clean_kwargs['amount'] = asset.price
            opp = Opportunity(
                id=get_id("Opportunity"),
                created_at=get_kst_now_naive(),
                updated_at=get_kst_now_naive(),
                **clean_kwargs
            )
            db.add(opp)
            db.commit()
            db.refresh(opp)
            return opp
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create opportunity: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def get_by_contact(db: Session, contact: str) -> List[Opportunity]:
        try:
            return db.query(Opportunity).filter(
                Opportunity.contact == contact,
                Opportunity.deleted_at == None
            ).all()
        except Exception as e:
            logger.error(f"Error fetching opportunities by contact {contact}: {str(e)}")
            return []

    @staticmethod
    @handle_agent_errors
    def get_opportunities(db: Session) -> List[Opportunity]:
        try:
            opps = db.query(Opportunity).filter(Opportunity.deleted_at == None).all()
            opps.sort(key=lambda x: make_naive_kst(x.created_at), reverse=True)
            return opps
        except Exception as e:
            logger.error(f"Error fetching all opportunities: {str(e)}")
            return []

    @staticmethod
    @handle_agent_errors
    def get_opportunity(db: Session, opp_id: str) -> Optional[Opportunity]:
        try:
            return db.query(Opportunity).filter(
                Opportunity.id == opp_id,
                Opportunity.deleted_at == None
            ).first()
        except Exception as e:
            logger.error(f"Error fetching opportunity {opp_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def update_opportunity(db: Session, opp_id: str, **kwargs) -> Optional[Opportunity]:
        try:
            opp = OpportunityService.get_opportunity(db, opp_id)
            if not opp:
                return None
            normalized_kwargs = OpportunityService._normalize_lookup_dependencies(db, opp, kwargs)
            force_null_fields = normalized_kwargs.pop("_force_null_fields", [])
            for key, value in normalized_kwargs.items():
                if hasattr(opp, key):
                    setattr(opp, key, value)
            for field in force_null_fields:
                if hasattr(opp, field):
                    setattr(opp, field, None)
            opp.updated_at = get_kst_now_naive()
            db.commit()
            db.refresh(opp)
            return opp
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update opportunity {opp_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def delete_opportunity(db: Session, opp_id: str, hard_delete: bool = False) -> bool:
        try:
            opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
            if not opp:
                return False
            if hard_delete:
                db.query(Lead).filter(Lead.converted_opportunity == opp_id).update({Lead.converted_opportunity: None}, synchronize_session=False)
                db.delete(opp)
            else:
                opp.deleted_at = get_kst_now_naive()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete opportunity {opp_id}: {str(e)}")
            return False

    @staticmethod
    @handle_agent_errors
    def restore_opportunity(db: Session, opp_id: str) -> bool:
        try:
            opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
            if not opp:
                return False
            opp.deleted_at = None
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to restore opportunity {opp_id}: {str(e)}")
            return False

    @staticmethod
    @handle_agent_errors
    def update_stage(db: Session, opp_id: str, stage: str) -> Optional[Opportunity]:
        try:
            return OpportunityService.update_opportunity(db, opp_id, stage=stage)
        except Exception as e:
            logger.error(f"Error updating stage for opportunity {opp_id}: {str(e)}")
            return None
    
    @staticmethod
    @handle_agent_errors
    def toggle_follow(db: Session, opp_id: str, enabled: bool) -> Optional[Opportunity]:
        try:
            return OpportunityService.update_opportunity(db, opp_id, is_followed=enabled)
        except Exception as e:
            logger.error(f"Error toggling follow for opportunity {opp_id}: {str(e)}")
            return None
    
    @staticmethod
    @handle_agent_errors
    def update_last_viewed(db: Session, opp_id: str) -> Optional[Opportunity]:
        try:
            return OpportunityService.update_opportunity(db, opp_id, last_viewed_at=get_kst_now_naive())
        except Exception as e:
            logger.error(f"Error updating last viewed for opportunity {opp_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def get_recent_clicked(db: Session, limit: int = 5) -> List[Opportunity]:
        try:
            opps = db.query(Opportunity).filter(
                Opportunity.deleted_at == None,
                Opportunity.last_viewed_at != None
            ).order_by(Opportunity.last_viewed_at.desc()).limit(limit).all()
            return opps
        except Exception as e:
            logger.error(f"Error fetching recent clicked opportunities: {str(e)}")
            return []

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
