from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from .lead_service import LeadService
from .opportunity_service import OpportunityService
from .contact_service import ContactService

from .base_service import BaseService
from backend.app.utils.timezone import get_kst_now_naive, make_naive_kst

logger = logging.getLogger(__name__)

class DashboardService:
    @staticmethod
    def get_dashboard_data(db: Session) -> Dict[str, Any]:
        """
        Gathers all necessary data for the dashboard.
        """
        # Recent Records (Mixed)
        # Fetch initial data
        leads = LeadService.get_leads(db)
        # Account is removed, so we don't fetch accounts here anymore
        # Fetch all opportunities early for performance stats
        all_opps = []
        try:
            all_opps = OpportunityService.get_opportunities(db)
        except Exception as e:
            logger.error(f"Error fetching all opportunities for dashboard: {e}")
            # Continue with an empty list if error occurs

        contacts = ContactService.get_contacts(db)
        
        all_records = []
        
        def safe_date(obj):
            dt = getattr(obj, 'created_at', None)
            return make_naive_kst(dt)

        # Populate all_records from leads, contacts
        for l in leads:
            all_records.append({"type": "Lead", "name": f"{l.first_name if l.first_name else ''} {l.last_name if l.last_name else ''}".strip() or "", "url": f"/leads/{l.id}", "date": safe_date(l)})
        for c in contacts: 
            all_records.append({"type": "Contact", "name": f"{c.first_name if c.first_name else ''} {c.last_name if c.last_name else ''}".strip() or c.name or "", "url": f"/contacts/{c.id}", "date": safe_date(c)})
        
        # Add opportunities to all_records if available
        for o in all_opps:
            all_records.append({"type": "Opportunity", "name": o.name, "url": f"/opportunities/{o.id}", "date": safe_date(o)})
        
        all_records.sort(key=lambda x: x["date"], reverse=True)
        
        # Filter opportunities for the last 7 days based on creation date (using KST for consistency)
        horizon_7_days_ago = get_kst_now_naive() - timedelta(days=7)
        
        recent_opps_created = []
        if all_opps: # Proceed only if all_opps was fetched successfully
            recent_opps_created = [o for o in all_opps if safe_date(o) >= horizon_7_days_ago]

        # Calculate performance stats from the filtered opportunities
        stages = ["Qualification", "Test Drive", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"]
        performance_by_stage = []
        for stage in stages:
            # Summing amounts, ensure amounts are handled correctly (e.g., not None and numeric)
            amount_sum = 0
            for o in recent_opps_created:
                if o.stage == stage:
                    try:
                        amount_sum += float(o.amount) if o.amount else 0
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid amount encountered for opportunity {o.id}: {o.amount}")
                        amount_sum += 0 # Treat invalid amounts as 0
            performance_by_stage.append({"label": stage, "amount": int(amount_sum)})
        
        # Calculate closed won amount safely
        closed_won_amount = 0
        try:
            closed_won_amount = int(sum(float(o.amount) for o in recent_opps_created if o.stage == 'Closed Won' and o.amount))
        except (ValueError, TypeError):
             logger.warning(f"Could not sum closed won amounts correctly.")

        performance = {
            "by_stage": performance_by_stage,
            "closed_won": f"{closed_won_amount:,}",
            "total_target": 1000000000 # Placeholder, actual target might be dynamic
        }

        recent_opps_clicked = []
        try:
            # Handle potential errors from these service calls
            recent_opps_clicked = OpportunityService.get_recent_clicked(db, limit=5)
        except Exception as e:
            logger.error(f"Error fetching recently clicked opportunities: {e}")
            # Continue with empty list if error occurs

        recommended_opps = []
        try:
            # Import from the modular ai_agent package
            from ai_agent.backend.recommendations import AIRecommendationService
            recommended_opps = AIRecommendationService.get_ai_recommendations(db, limit=5)
        except Exception as e:
            logger.error(f"Error fetching AI recommended opportunities: {e}")
            # Continue with empty list if error occurs

        return {
            "recent_records": all_records[:5],
            "opportunities": recent_opps_clicked,
            "recommended_opportunities": recommended_opps,
            "performance": performance
        }
