import os
import sys

# Add development to PYTHONPATH
sys.path.insert(0, os.path.abspath('.gemini/development'))

from unittest.mock import patch
from db.database import SessionLocal
from backend.app.services.contact_service import ContactService
from backend.app.services.lead_service import LeadService
from backend.app.services.opportunity_service import OpportunityService
from backend.app.services.product_service import ProductService
from backend.app.services.asset_service import AssetService
from backend.app.services.vehicle_spec_service import VehicleSpecService
from backend.app.services.model_service import ModelService
from backend.app.services.message_template_service import MessageTemplateService
from backend.app.services.messaging_service import MessagingService
from backend.app.services.surem_service import SureMService

def run_crud_and_messaging():
    db = SessionLocal()
    print("=== Starting E2E CRUD & Messaging Simulation ===")

    try:
        # 1. Contact CRUD
        print("\n[Contact] Creating Contact...")
        contact = ContactService.create_contact(db, first_name="E2E", last_name="Test", phone="010-1234-5678", email="e2e@test.com")
        print(f"[Contact] Created: {contact.id}")
        ContactService.update_contact(db, contact.id, description="Updated Contact")
        print(f"[Contact] Updated Description.")

        # 2. Lead CRUD
        print("\n[Lead] Creating Lead...")
        lead = LeadService.create_lead(db, first_name="Lead", last_name="User", phone="010-0000-0000", status="New")
        print(f"[Lead] Created: {lead.id}")
        LeadService.update_lead(db, lead.id, status="Working")
        print(f"[Lead] Updated Status.")

        # 3. Product & Brand & Model
        print("\n[Vehicle Specs] Creating Brand & Model...")
        brand = VehicleSpecService.create_spec(db, name="E2E Brand", record_type="Brand")
        model = ModelService.create_model(db, name="E2E Model", brand=brand.id)
        
        print("\n[Product] Creating Product...")
        product = ProductService.create_product(db, name="E2E Product", brand=brand.id, model=model.id, base_price=50000.0)
        print(f"[Product] Created: {product.id}")

        # 4. Opportunity & Asset
        print("\n[Opportunity] Creating Opportunity...")
        opp = OpportunityService.create_opportunity(db, name="E2E Opp", contact=contact.id, amount=1000.0, stage="Prospecting")
        print(f"[Opportunity] Created: {opp.id}")
        
        print("\n[Asset] Creating Asset...")
        asset = AssetService.create_asset(db, name="E2E Asset", contact=contact.id, product=product.id, vin="VIN123456")
        print(f"[Asset] Created: {asset.id}")

        # 5. Message Template
        print("\n[Message Template] Creating Templates...")
        sms_tpl = MessageTemplateService.create_template(db, name="SMS Tpl", record_type="SMS", content="SMS Body")
        lms_tpl = MessageTemplateService.create_template(db, name="LMS Tpl", record_type="LMS", subject="LMS Sub", content="LMS Body "*10)
        mms_tpl = MessageTemplateService.create_template(db, name="MMS Tpl", record_type="MMS", subject="MMS Sub", content="MMS Body")

        # 6. Messaging Simulation (Mocking the actual SureM API)
        print("\n[Messaging] Sending SMS, LMS, MMS (Simulating button clicks)...")
        with patch.object(SureMService, 'send_sms', return_value={"status": "success", "code": "A0000"}):
            msg_sms = MessagingService.send_message(db, contact_id=contact.id, content=sms_tpl.content, record_type="SMS")
            print(f"[Messaging] SMS Sent! Message ID: {msg_sms.id}, Status: {msg_sms.status}")
            
        with patch.object(SureMService, 'send_mms', return_value={"status": "success", "code": "A0000"}):
            msg_lms = MessagingService.send_message(db, contact_id=contact.id, content=lms_tpl.content, record_type="LMS")
            print(f"[Messaging] LMS Sent! Message ID: {msg_lms.id}, Status: {msg_lms.status}")

        with patch.object(SureMService, 'send_mms', return_value={"status": "success", "code": "A0000"}):
            msg_mms = MessagingService.send_message(db, contact_id=contact.id, content=mms_tpl.content, record_type="MMS")
            print(f"[Messaging] MMS Sent! Message ID: {msg_mms.id}, Status: {msg_mms.status}")

        # 7. Cleanup (Delete)
        print("\n[Cleanup] Deleting all created E2E records...")
        AssetService.delete_asset(db, asset.id)
        OpportunityService.delete_opportunity(db, opp.id)
        ProductService.delete_product(db, product.id)
        ModelService.delete_model(db, model.id)
        VehicleSpecService.delete_vehicle_spec(db, brand.id)
        LeadService.delete_lead(db, lead.id)
        ContactService.delete_contact(db, contact.id)
        MessageTemplateService.delete_template(db, sms_tpl.id)
        MessageTemplateService.delete_template(db, lms_tpl.id)
        MessageTemplateService.delete_template(db, mms_tpl.id)
        print("[Cleanup] Done.")
        print("=== E2E Simulation Completed Successfully ===")

    except Exception as e:
        print(f"Error during E2E simulation: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_crud_and_messaging()
