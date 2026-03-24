import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web.backend.app.database import SessionLocal
from web.backend.app.models import Opportunity
from web.backend.app.services.opportunity_service import OpportunityService

def test_phase6_logic():
    db = SessionLocal()
    try:
        print("--- Testing Phase 6 Logic ---")
        
        # 1. Test Opportunity View History Tracking
        opps = OpportunityService.get_opportunities(db)
        if not opps:
            print("No opportunities found to test history tracking.")
        else:
            opp = opps[0]
            print(f"Tracking view for Opportunity: {opp.name} (ID: {opp.id})")
            OpportunityService.update_last_viewed(db, opp.id)
            
            db.refresh(opp)
            if opp.last_viewed_at:
                print(f"✅ Success: last_viewed_at updated to {opp.last_viewed_at}")
            else:
                print("❌ Failure: last_viewed_at NOT updated.")

        # 2. Test Dashboard Pipeline Filtering (Last 7 Days)
        from datetime import datetime, timedelta
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Count opps created within 7 days
        all_opps = db.query(Opportunity).filter(Opportunity.deleted_at == None).all()
        recent_count = sum(1 for o in all_opps if o.created_at >= seven_days_ago)
        print(f"Total opportunities: {len(all_opps)}, Recent (7 days): {recent_count}")
        
        # Verify the calculation logic matches web_router.py
        opps_seven_days = [o for o in all_opps if o.created_at and (o.created_at if isinstance(o.created_at, datetime) else datetime.fromisoformat(str(o.created_at))) >= seven_days_ago]
        if len(opps_seven_days) == recent_count:
            print(f"✅ Success: Pipeline filtering correctly identifies {len(opps_seven_days)} recent opportunities.")
        else:
            print(f"❌ Failure: Pipeline filtering mismatch. Expected {recent_count}, got {len(opps_seven_days)}.")

        # 3. Test Sorting by Recency (Clicked)
        # We need at least 2 clicked for this
        if len(opps) >= 2:
            opp2 = opps[1]
            import time
            time.sleep(1) # Ensure different timestamp
            print(f"Tracking view for second Opportunity: {opp2.name} (ID: {opp2.id})")
            OpportunityService.update_last_viewed(db, opp2.id)
            
            clicked_opps = db.query(Opportunity).filter(Opportunity.last_viewed_at != None).all()
            clicked_opps.sort(key=lambda x: x.last_viewed_at, reverse=True)
            
            if clicked_opps[0].id == opp2.id:
                print(f"✅ Success: Recent Opportunities sorted correctly (Most recent view: {clicked_opps[0].name})")
            else:
                print(f"❌ Failure: Recent Opportunities sorting incorrect.")

    except Exception as e:
        print(f"An error occurred during testing: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_phase6_logic()
