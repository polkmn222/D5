import pytest
import uuid
from db.database import Base, engine, SessionLocal
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.opportunity_service import OpportunityService
from db.models import Lead, Opportunity

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_lead_atomic_operations(db):
    suffix = uuid.uuid4().hex[:6]
    # Create lead
    lead = LeadService.create_lead(
        db, 
        first_name="Atomic", 
        last_name=f"Lead_{suffix}", 
        email=f"atomic_{suffix}@example.com",
        status="New"
    )
    assert lead.id is not None
    assert lead.is_followed is False
    # Test update_stage
    LeadService.update_stage(db, lead.id, "Follow Up")
    db.refresh(lead)
    assert lead.status == "Follow Up"
    
    # Test toggle_follow
    LeadService.toggle_follow(db, lead.id, True)
    db.refresh(lead)
    assert lead.is_followed is True
    
    LeadService.toggle_follow(db, lead.id, False)
    db.refresh(lead)
    assert lead.is_followed is False

def test_opportunity_atomic_operations(db):
    suffix = uuid.uuid4().hex[:6]
    # Create opportunity
    opp = OpportunityService.create_opportunity(
        db, 
        contact=None, 
        name=f"Atomic Deal {suffix}", 
        amount=1000000, 
        stage="Prospecting"
    )
    assert opp.id is not None
    assert opp.is_followed is False
    
    # Test update_stage
    OpportunityService.update_stage(db, opp.id, "Qualification")
    db.refresh(opp)
    assert opp.stage == "Qualification"
    
    # Test toggle_follow
    OpportunityService.toggle_follow(db, opp.id, True)
    db.refresh(opp)
    assert opp.is_followed is True
