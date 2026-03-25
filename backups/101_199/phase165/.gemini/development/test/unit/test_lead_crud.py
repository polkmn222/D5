import pytest
import uuid
from db.database import Base, engine, SessionLocal
from db.models import Lead
from backend.app.services.lead_service import LeadService

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_lead_lifecycle(db):
    suffix = uuid.uuid4().hex[:6]
    # 1. Create
    lead = LeadService.create_lead(
        db, first_name="Lead", last_name=f"Tester_{suffix}", 
        email=f"lead_{suffix}@example.com"
    )
    assert lead.id.startswith("00Q")
    
    # 2. Update
    updated = LeadService.update_lead(db, lead.id, status="Follow Up")
    assert updated.status == "Follow Up"
    
    # 3. Delete
    success = LeadService.delete_lead(db, lead.id)
    assert success is True
    
    retrieved = LeadService.get_lead(db, lead.id)
    assert retrieved is None
