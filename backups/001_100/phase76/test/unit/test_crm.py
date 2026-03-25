import pytest
from db.database import Base, engine, SessionLocal
from db.models import Contact, Lead, Opportunity
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.contact_service import ContactService
from web.backend.app.utils.sf_id import get_id

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_sf_id_generation():
    contact_id = get_id("Contact")
    assert len(contact_id) == 18
    assert contact_id.startswith("003")
    
    opp_id = get_id("Opportunity")
    assert len(opp_id) == 18
    assert opp_id.startswith("006")

def test_lead_conversion(db):
    import uuid
    suffix = uuid.uuid4().hex[:6]
    first_name = f"John_{suffix}"
    last_name = "Doe"
    
    # 1. Create a Lead
    lead = LeadService.create_lead(
        db, first_name=first_name, last_name=last_name, 
        email=f"john_{suffix}@test.com", gender="Male"
    )
    assert lead.id.startswith("00Q")
    
    # 2. Convert Lead
    LeadService.convert_lead_advanced(db, lead.id, name=f"{first_name} {last_name}")
    
    # 3. Verify Contact and Opportunity
    contact = db.query(Contact).filter(Contact.name == f"{first_name} {last_name}").first()
    assert contact is not None
    assert contact.id.startswith("003")
    
    opp = db.query(Opportunity).filter(Opportunity.contact == contact.id).first()
    assert opp is not None
    assert opp.id.startswith("006")
