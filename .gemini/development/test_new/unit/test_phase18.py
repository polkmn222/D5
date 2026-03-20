import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from backend.app.services.lead_service import LeadService
from backend.app.services.opportunity_service import OpportunityService
from backend.app.services.contact_service import ContactService
from backend.app.services.vehicle_spec_service import VehicleSpecService
from datetime import datetime
import time

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase18.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_lead_update_and_soft_delete(db):
    # Create with required fields (email, phone etc depending on schema)
    # Using 'test@example.com' to satisfy NOT NULL constraints
    lead = LeadService.create_lead(db, first_name="Test", last_name="Lead", phone="010-0000-0000", email="test@example.com")
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
    # Create Contact first
    contact = ContactService.create_contact(db, first_name="Test", last_name="User", email="test@user.com")
    
    # Create Opp
    opp = OpportunityService.create_opportunity(db, contact=contact.id, name="Test Opp", amount=1000, stage="Prospecting")
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
    # Verify prefix and retrieval
    spec = VehicleSpecService.create_spec(db, name="Test Brand", record_type="Brand")
    assert spec.id.startswith("avS")
    
    retrieved = VehicleSpecService.get_vehicle_spec(db, spec.id)
    assert retrieved.name == "Test Brand"
    
    specs = VehicleSpecService.get_vehicle_specs(db, record_type="Brand")
    assert len(specs) == 1
