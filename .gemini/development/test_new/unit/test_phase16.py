import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from backend.app.services.lead_service import LeadService
from backend.app.services.opportunity_service import OpportunityService
from db.models import Lead, Opportunity

# Use a separate test database file
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_phase16.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_lead_atomic_operations(db):
    # Create lead
    lead = LeadService.create_lead(
        db, 
        first_name="Atomic", 
        last_name="Lead", 
        email="atomic@example.com",
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
    # Create opportunity
    opp = OpportunityService.create_opportunity(
        db, 
        contact="CON_123", 
        name="Atomic Deal", 
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
