import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add the project root to sys.path
sys.path.append('/Users/sangyeol.park@gruve.ai/D4')

from backend.app.database import Base, SQLALCHEMY_DATABASE_URL
from backend.app.models import Lead, Account, Contact, Opportunity
from backend.app.services.lead_service import LeadService
from backend.app.utils.sf_id import get_id

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_lead_conversion_logic():
    db = SessionLocal()
    try:
        print("--- Starting Lead Conversion Test ---")
        
        # 1. Create a dummy lead
        lead_id = get_id("Lead")
        lead = Lead(
            id=lead_id,
            first_name="Test",
            last_name="ConvertedLead",
            email="converted@example.com",
            phone="010-1234-5678",
            status="New",
            is_converted=False
        )
        db.add(lead)
        db.commit()
        print(f"Created Lead: {lead.id}")

        # 2. Convert the lead
        print("Converting lead...")
        result = LeadService.convert_lead_advanced(
            db, lead_id=lead.id,
            account_name="Converted Account",
            account_record_type="Corporate",
            opportunity_name="Converted Opportunity"
        )

        if result:
            print("Conversion result details:")
            print(f"- Account: {result['account'].id} ({result['account'].name})")
            print(f"- Contact: {result['contact'].id} ({result['contact'].first_name} {result['contact'].last_name})")
            if result['opportunity']:
                print(f"- Opportunity: {result['opportunity'].id} ({result['opportunity'].name})")
            
            # 3. Verify Lead status
            db.refresh(lead)
            print(f"Lead is_converted: {lead.is_converted}")
            print(f"Lead status: {lead.status}")
            
            if lead.is_converted and lead.status == "Qualified":
                print("\n[SUCCESS] Lead conversion logic verified correctly.")
            else:
                print("\n[FAILURE] Lead status was not updated correctly.")
        else:
            print("\n[FAILURE] Lead conversion returned None.")

    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
    finally:
        # Cleanup
        # Optionally delete the test records here if needed
        db.close()

if __name__ == "__main__":
    test_lead_conversion_logic()
