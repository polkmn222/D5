from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from db.models import Opportunity
from backend.app.utils.timezone import get_kst_now_naive, make_naive_kst
from .base_service import BaseService
from backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class OpportunityService(BaseService[Opportunity]):
    model = Opportunity
    object_name = "Opportunity"

    @classmethod
    @handle_agent_errors
    def create_opportunity(cls, db: Session, contact: str = None, name: str = "", amount: int = 0, stage: str = "Prospecting", status: str = "Open", probability: int = 10, **kwargs) -> Opportunity:
        try:
            # Sync amount with asset price if asset is provided
            from .asset_service import AssetService
            asset_id = kwargs.get('asset')
            if asset_id:
                asset = AssetService.get_asset(db, asset_id)
                if asset and asset.price:
                    amount = asset.price
            
            return cls.create(db, contact=contact, name=name, amount=amount, stage=stage, status=status, probability=probability, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in create_opportunity: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def get_by_contact(cls, db: Session, contact: str) -> List[Opportunity]:
        try:
            return cls.list(db, contact=contact)
        except Exception as e:
            logger.error(f"Error in get_by_contact: {e}")
            return []

    @classmethod
    @handle_agent_errors
    def get_opportunities(cls, db: Session) -> List[Opportunity]:
        try:
            opps = cls.list(db)
            opps.sort(key=lambda x: make_naive_kst(x.created_at), reverse=True)
            return opps
        except Exception as e:
            logger.error(f"Error in get_opportunities: {e}")
            return []

    @classmethod
    @handle_agent_errors
    def get_opportunity(cls, db: Session, opp_id: str) -> Optional[Opportunity]:
        try:
            return cls.get(db, opp_id)
        except Exception as e:
            logger.error(f"Error in get_opportunity: {e}")
            return None

    @classmethod
    @handle_agent_errors
    def update_opportunity(cls, db: Session, opp_id: str, **kwargs) -> Optional[Opportunity]:
        try:
            # Sync amount with asset price if asset is updated or already exists
            from .asset_service import AssetService
            
            # Check if 'asset' key exists in kwargs (it might be None or empty string if cleared)
            if 'asset' in kwargs:
                asset_id = kwargs.get('asset')
                if asset_id:
                    asset = AssetService.get_asset(db, asset_id)
                    if asset and asset.price:
                        kwargs['amount'] = asset.price
            
            return cls.update(db, opp_id, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in update_opportunity: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def delete_opportunity(cls, db: Session, opp_id: str) -> bool:
        try:
            return cls.delete(db, opp_id)
        except Exception as e:
            logger.error(f"Critical error in delete_opportunity: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def restore_opportunity(cls, db: Session, opp_id: str) -> bool:
        try:
            return cls.restore(db, opp_id)
        except Exception as e:
            logger.error(f"Critical error in restore_opportunity: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def update_stage(cls, db: Session, opp_id: str, stage: str) -> Optional[Opportunity]:
        try:
            return cls.update(db, opp_id, stage=stage)
        except Exception as e:
            logger.error(f"Critical error in update_stage: {e}")
            raise e
    
    @classmethod
    @handle_agent_errors
    def toggle_follow(cls, db: Session, opp_id: str, enabled: bool) -> Optional[Opportunity]:
        try:
            return cls.update(db, opp_id, is_followed=enabled)
        except Exception as e:
            logger.error(f"Critical error in toggle_follow: {e}")
            raise e
    
    @classmethod
    @handle_agent_errors
    def update_last_viewed(cls, db: Session, opp_id: str) -> Optional[Opportunity]:
        try:
            return cls.update(db, opp_id, last_viewed_at=get_kst_now_naive())
        except Exception as e:
            logger.error(f"Critical error in update_last_viewed: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def get_recent_clicked(cls, db: Session, limit: int = 5) -> List[Opportunity]:
        try:
            opps = cls.list(db)
            # Filter for opportunities that have been viewed
            viewed_opps = [o for o in opps if o.last_viewed_at]
            
            # Sort the viewed opportunities by creation date in reverse chronological order
            viewed_opps.sort(key=lambda x: make_naive_kst(x.created_at), reverse=True)
            
            return viewed_opps[:limit]
        except Exception as e:
            logger.error(f"Error in get_recent_clicked: {e}")
            return []

    @classmethod
    @handle_agent_errors
    def get_performance_stats(cls, db: Session, horizon_days: int = 7) -> dict:
        try:
            horizon = get_kst_now_naive() - timedelta(days=horizon_days)
            opps = cls.list(db)
            
            opps_filtered = [o for o in opps if make_naive_kst(o.created_at) >= horizon]
            
            stages = ["Qualification", "Test Drive", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"]
            performance_by_stage = []
            for stage in stages:
                amount = sum(o.amount for o in opps_filtered if o.stage == stage and o.amount)
                performance_by_stage.append({"label": stage, "amount": int(amount)})
            
            closed_won_amount = sum(o.amount for o in opps_filtered if o.stage == 'Closed Won' and o.amount)
            
            return {
                "by_stage": performance_by_stage,
                "closed_won": f"{int(closed_won_amount):,}",
                "total_target": 1000000000
            }
        except Exception as e:
            logger.error(f"Error in get_performance_stats: {e}")
            return {"by_stage": [], "closed_won": "0", "total_target": 1000000000}

# AI recommendations moved to ai_agent.backend.recommendations


# AI recommendations moved to ai_agent.backend.recommendations
