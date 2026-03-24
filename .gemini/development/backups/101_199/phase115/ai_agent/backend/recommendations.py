from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from db.models import Opportunity, Contact, Model
from web.backend.app.utils.timezone import get_kst_now_naive, make_naive_kst
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class AIRecommendationService:
    # Global state for current preference (simple implementation)
    CURRENT_MODE = "Hot Deals" # Default mode
    SENDABLE_RECOMMENDATION_LIMIT = 15

    @staticmethod
    def user_facing_mode_label(mode: Optional[str]) -> str:
        return "New Records" if mode == "Default" else (mode or "New Records")

    @staticmethod
    def normalize_temperature_label(value: Optional[str], fallback: str = "Cold") -> str:
        normalized = (value or "").strip().lower()
        mapping = {
            "hot": "Hot",
            "urgent": "Hot",
            "warm": "Warm",
            "gold": "Warm",
            "cold": "Cold",
            "new": "Cold",
        }
        if not normalized:
            return fallback
        return mapping.get(normalized, fallback)

    @classmethod
    @handle_agent_errors
    def get_ai_recommendations(cls, db: Session, limit: int = 10, mode: Optional[str] = None) -> List[Opportunity]:
        """
        AI-driven logic to recommend opportunities based on specific modes.
        """
        try:
            target_mode = mode or cls.CURRENT_MODE
            
            query = db.query(Opportunity)\
                .join(Contact, Opportunity.contact == Contact.id)\
                .join(Model, Opportunity.model == Model.id)\
                .filter(Opportunity.deleted_at == None, Contact.deleted_at == None)

            # Get reference date
            reference_date = get_kst_now_naive()
            horizon_7d = reference_date - timedelta(days=7)
            horizon_30d = reference_date - timedelta(days=30)

            recommends = []
            
            if target_mode == "Hot Deals":
                # Current Logic: Test Drive in last 7 days
                all_opps = query.all()
                for o in all_opps:
                    o_created = make_naive_kst(o.created_at)
                    if o.stage and o.stage.lower() == "test drive" and o_created >= horizon_7d:
                        o.temp_display = cls.normalize_temperature_label("Hot")
                        recommends.append(o)
                recommends.sort(key=lambda x: x.created_at or get_kst_now_naive(), reverse=True)

            elif target_mode == "Follow Up":
                # Logic: active opportunities that were updated after creation in the last 30 days
                all_opps = query.filter(~Opportunity.stage.in_(["Test Drive", "Closed Won", "Closed Lost"])).all()
                for o in all_opps:
                    updated_at = make_naive_kst(o.updated_at) if o.updated_at else None
                    created_at = make_naive_kst(o.created_at) if o.created_at else None
                    if not updated_at or not created_at or updated_at < horizon_30d:
                        continue
                    if updated_at <= created_at:
                        continue
                    o.temp_display = cls.normalize_temperature_label("Warm")
                    recommends.append(o)
                recommends.sort(key=lambda x: x.updated_at or x.created_at or get_kst_now_naive(), reverse=True)

            elif target_mode == "Closing Soon":
                # Logic: In Negotiation/Review stage
                recommends = query.filter(Opportunity.stage.in_(["Negotiation/Review", "Proposal/Price Quote"]))\
                                  .order_by(Opportunity.updated_at.desc())\
                                  .all()
                for o in recommends:
                    o.temp_display = cls.normalize_temperature_label("Urgent")
            
            else:
                # Default fallback
                recommends = query.order_by(Opportunity.created_at.desc()).limit(limit).all()
                for o in recommends:
                    o.temp_display = cls.normalize_temperature_label("New")

            return recommends[:limit]
        except Exception as e:
            logger.error(f"Error in AIRecommendationService.get_ai_recommendations: {e}")
            return []

    @classmethod
    def get_sendable_recommendations(cls, db: Session, limit: int = SENDABLE_RECOMMENDATION_LIMIT, scan_limit: int = 50) -> List[Opportunity]:
        sendable: List[Opportunity] = []
        for opp in cls.get_ai_recommendations(db, limit=max(limit, scan_limit)):
            if len(sendable) >= limit:
                break

            if not getattr(opp, "model", None):
                continue

            contact = db.query(Contact).filter(Contact.id == opp.contact, Contact.deleted_at == None).first()
            if not contact or not getattr(contact, "phone", None):
                continue

            model = db.query(Model).filter(Model.id == opp.model).first()
            if not model:
                continue

            sendable.append(opp)

        return sendable

    @classmethod
    def set_recommendation_mode(cls, mode: str):
        aliases = {"New Records": "Default"}
        mode = aliases.get(mode, mode)
        valid_modes = ["Hot Deals", "Follow Up", "Closing Soon", "Default"]
        if mode in valid_modes:
            cls.CURRENT_MODE = mode
            return True
        return False

    @classmethod
    def get_recommendation_mode(cls) -> str:
        return cls.CURRENT_MODE
