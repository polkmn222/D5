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
        mapping = {
            "Default": "New Records",
            "Closing Soon": "Closed Won",
        }
        return mapping.get(mode, mode or "New Records")

    @classmethod
    def refresh_opportunity_temperatures(cls, db: Session) -> None:
        reference_date = get_kst_now_naive()
        month_horizon = reference_date - timedelta(days=30)
        opportunities = db.query(Opportunity).filter(Opportunity.deleted_at == None).all()

        for opp in opportunities:
            stage = (getattr(opp, "stage", "") or "").strip().lower()
            status = (getattr(opp, "status", "") or "").strip().lower()
            created_at = getattr(opp, "created_at", None)
            created_kst = make_naive_kst(created_at) if created_at else None

            if stage == "test drive":
                opp.temperature = "Hot"
            elif status == "closed lost" or stage == "closed lost" or (created_kst and created_kst < month_horizon):
                opp.temperature = "Cold"
            else:
                opp.temperature = "Warm"

        db.commit()

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
            cls.refresh_opportunity_temperatures(db)
            
            query = db.query(Opportunity)\
                .join(Contact, Opportunity.contact == Contact.id)\
                .join(Model, Opportunity.model == Model.id)\
                .filter(Opportunity.deleted_at == None, Contact.deleted_at == None)

            reference_date = get_kst_now_naive()
            horizon_7d = reference_date - timedelta(days=7)
            horizon_30d = reference_date - timedelta(days=30)

            recommends = []
            
            if target_mode == "Hot Deals":
                all_opps = query.filter(Opportunity.stage == "Test Drive").all()
                for o in all_opps:
                    created_at = make_naive_kst(getattr(o, "created_at", None)) if getattr(o, "created_at", None) else None
                    if created_at and created_at >= horizon_7d:
                        o.temp_display = cls.normalize_temperature_label(getattr(o, "temperature", None))
                        recommends.append(o)
                recommends.sort(key=lambda x: x.created_at or get_kst_now_naive(), reverse=True)

            elif target_mode == "Follow Up":
                all_opps = query.filter(
                    Opportunity.is_followed == True,
                    ~Opportunity.stage.in_(["Closed Won", "Closed Lost"]),
                ).all()
                for o in all_opps:
                    o.temp_display = cls.normalize_temperature_label(getattr(o, "temperature", None))
                    recommends.append(o)
                recommends.sort(key=lambda x: x.updated_at or x.created_at or get_kst_now_naive(), reverse=True)

            elif target_mode == "Closing Soon":
                all_opps = query.filter(Opportunity.stage == "Closed Won").all()
                for o in all_opps:
                    closed_source = getattr(o, "close_date", None) or getattr(o, "created_at", None)
                    closed_at = make_naive_kst(closed_source) if closed_source else None
                    if closed_at and closed_at >= horizon_7d:
                        o.temp_display = cls.normalize_temperature_label(getattr(o, "temperature", None))
                        recommends.append(o)
                recommends.sort(key=lambda x: x.updated_at or x.created_at or get_kst_now_naive(), reverse=True)
            
            else:
                recommends = query.filter(~Opportunity.stage.in_(["Closed Won", "Closed Lost"]))\
                                  .order_by(Opportunity.created_at.desc())\
                                  .all()
                for o in recommends:
                    o.temp_display = cls.normalize_temperature_label(getattr(o, "temperature", None))

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
        aliases = {"New Records": "Default", "Closed Won": "Closing Soon"}
        mode = aliases.get(mode, mode)
        valid_modes = ["Hot Deals", "Follow Up", "Closing Soon", "Default"]
        if mode in valid_modes:
            cls.CURRENT_MODE = mode
            return True
        return False

    @classmethod
    def get_recommendation_mode(cls) -> str:
        return cls.CURRENT_MODE
