import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from db.models import Contact, Lead, Opportunity
from backend.app.services.lead_service import LeadService
from backend.app.services.contact_service import ContactService
from backend.app.utils.sf_id import get_id

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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

def test_sf_id_generation():
    contact_id = get_id("Contact")
    assert len(contact_id) == 18
    assert contact_id.startswith("003")
    
    opp_id = get_id("Opportunity")
    assert len(opp_id) == 18
    assert opp_id.startswith("006")

def test_lead_conversion(db):
    # 1. Create a Lead (Company removed in Phase 10)
    lead = LeadService.create_lead(
        db, first_name="John", last_name="Doe", 
        email="john@tesla.com", gender="Male"
    )
    assert lead.id.startswith("00Q")
    
    # 2. Convert Lead
    LeadService.convert_lead(db, lead.id)
    
    # 3. Verify Contact and Opportunity
    contact = db.query(Contact).filter(Contact.name == "John Doe").first()
    assert contact is not None
    assert contact.id.startswith("003")
    
    opp = db.query(Opportunity).filter(Opportunity.contact == contact.id).first()
    assert opp is not None
    assert opp.id.startswith("006")
