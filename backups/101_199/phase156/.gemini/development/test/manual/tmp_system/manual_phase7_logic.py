import os
import sys
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal
from backend.app.models import Account, Lead
from backend.app.services.account_service import AccountService
from backend.app.services.lead_service import LeadService

def test_phase7_logic():
    db = SessionLocal()
    try:
        print("--- Testing Phase 7 Logic ---")
        
        # 1. Test Account Field Expansion
        print("Testing Account field expansion (phone/email)...")
        test_acc = AccountService.create_account(
            db, 
            name="Test Account PhoneEmail", 
            phone="010-1234-5678", 
            email="test@account.com"
        )
        if test_acc.phone == "010-1234-5678" and test_acc.email == "test@account.com":
            print(f"✅ Success: Account created with phone {test_acc.phone} and email {test_acc.email}")
        else:
            print(f"❌ Failure: Account fields NOT preserved. Phone: {test_acc.phone}, Email: {test_acc.email}")

        # 2. Test Lead to Account Data Flow (Conversion)
        print("Testing Lead conversion data flow...")
        test_lead = LeadService.create_lead(
            db, 
            first_name="Lead", 
            last_name="ConvertTest", 
            phone="010-9999-8888", 
            email="convert@lead.com"
        )
        
        # Convert lead
        result = LeadService.convert_lead_advanced(
            db, 
            test_lead.id, 
            account_name="Converted Account", 
            account_record_type="Corporate"
        )
        
        if result and "account" in result:
            acc = result["account"]
            if acc.phone == "010-9999-8888" and acc.email == "convert@lead.com":
                print(f"✅ Success: Data flowed correctly from Lead to Account. Phone: {acc.phone}, Email: {acc.email}")
            else:
                print(f"❌ Failure: Data flow mismatch. Account Phone: {acc.phone}, Lead Phone: {test_lead.phone}")
        else:
            print("❌ Failure: Lead conversion failed returned no result.")

    except Exception as e:
        print(f"An error occurred during testing: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_phase7_logic()
