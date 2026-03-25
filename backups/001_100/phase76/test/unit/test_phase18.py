import pytest
import uuid
import time
from db.database import Base, engine, SessionLocal
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_lead_update_and_soft_delete(db):
    suffix = uuid.uuid4().hex[:6]
    # Create with required fields
    lead = LeadService.create_lead(db, first_name="Test", last_name=f"Lead_{suffix}", phone="010-0000-0000", email=f"test_{suffix}@example.com")
    assert lead.id.startswith("00Q")
    created_at = lead.created_at
    
    # Wait a bit
    time.sleep(0.1)
    
    # Update
    updated_lead = LeadService.update_lead(db, lead.id, first_name="Updated")
    assert updated_lead.first_name == "Updated"
    assert updated_lead.updated_at > created_at
    
    # Soft Delete
    LeadService.delete_lead(db, lead.id)
    retrieved = LeadService.get_lead(db, lead.id)
    assert retrieved is None

def test_opportunity_stage_and_dates(db):
    suffix = uuid.uuid4().hex[:6]
    # Create Contact first
    contact = ContactService.create_contact(db, first_name="Test", last_name=f"User_{suffix}", email=f"test_{suffix}@user.com")
    
    # Create Opp
    opp = OpportunityService.create_opportunity(db, contact=contact.id, name=f"Test Opp {suffix}", amount=1000, stage="Prospecting")
    assert opp.stage == "Prospecting"
    
    # Update Stage
    OpportunityService.update_stage(db, opp.id, "Qualification")
    assert opp.stage == "Qualification"
    
    # Verify updated_at logic in generic update
    old_update = opp.updated_at
    time.sleep(0.1)
    OpportunityService.update_opportunity(db, opp.id, amount=2000)
    assert opp.amount == 2000
    assert opp.updated_at > old_update

def test_vehicle_spec_service_naming(db):
    suffix = uuid.uuid4().hex[:6]
    # Verify prefix and retrieval
    spec = VehicleSpecService.create_spec(db, name=f"Test Brand {suffix}", record_type="Brand")
    assert spec.id.startswith("avS")
    
    retrieved = VehicleSpecService.get_vehicle_spec(db, spec.id)
    assert retrieved.name == f"Test Brand {suffix}"
    
    specs = VehicleSpecService.get_vehicle_specs(db, record_type="Brand")
    assert any(s.id == spec.id for s in specs)
