from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import logging
from db.models import Opportunity, Contact, Model
from backend.app.utils.timezone import get_kst_now_naive, make_naive_kst
from backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class AIRecommendationService:
    @classmethod
    @handle_agent_errors
    def get_ai_recommendations(cls, db: Session, limit: int = 10) -> List[Opportunity]:
        """
        AI-driven logic to recommend hot opportunities.
        """
        try:
            # Fetch only Opportunities where the associated Contact has a phone number AND has an associated Model
            all_opps = db.query(Opportunity)\
                .join(Contact, Opportunity.contact == Contact.id)\
                .join(Model, Opportunity.model == Model.id)\
                .filter(Opportunity.deleted_at == None, Contact.deleted_at == None)\
                .filter(Contact.phone != None, Contact.phone != "")\
                .all()
                
            # Get the latest creation date in the system to calculate the 7-day window
            latest_opp = db.query(Opportunity).order_by(Opportunity.created_at.desc()).first()
            if not latest_opp or not latest_opp.created_at:
                reference_date = get_kst_now_naive()
            else:
                reference_date = make_naive_kst(latest_opp.created_at)

            horizon_7d = reference_date - timedelta(days=7)
            
            recommends = []
            for o in all_opps:
                created_at = make_naive_kst(o.created_at)
                
                # MANDATE: "Test Drive" (or "Test drive") within 7 days regardless of amount
                is_test_drive = o.stage.lower() == "test drive" if o.stage else False
                
                if is_test_drive and created_at >= horizon_7d:
                    o.temp_display = "Hot"
                    recommends.append(o)
                    continue

                # Fallback logic for other high-value deals if needed
                if o.stage == "Closed Won" and created_at >= horizon_7d:
                    o.temp_display = "Warm"
                    recommends.append(o)
                    
            # Sort by creation date descending
            recommends.sort(key=lambda x: make_naive_kst(x.created_at), reverse=True)
            return recommends[:limit]
        except Exception as e:
            logger.error(f"Error in AIRecommendationService.get_ai_recommendations: {e}")
            return []
