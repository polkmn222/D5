import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from backend.app.services.lead_service import LeadService

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_lead_crud.db"
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

def test_lead_lifecycle(db):
    # Create
    lead = LeadService.create_lead(
        db, 
        first_name="Test", 
        last_name="Lead", 
        email="test@example.com",
        status="New"
    )
    assert lead.id is not None
    lead_id = lead.id
    
    # Get
    fetched = LeadService.get_lead(db, lead_id)
    assert fetched is not None
    assert fetched.first_name == "Test"
    
    # Update
    updated = LeadService.update_lead(db, lead_id, first_name="Updated", id="HACKED_ID")
    assert updated.first_name == "Updated"
    assert updated.id == lead_id # Should NOT be changed
    
    # List
    leads = LeadService.get_leads(db)
    assert len(leads) == 1
    
    # Delete
    success = LeadService.delete_lead(db, lead_id)
    assert success is True
    
    # Get after delete (Soft delete)
    deleted = LeadService.get_lead(db, lead_id)
    assert deleted is None
    
    # Restore
    success = LeadService.restore_lead(db, lead_id)
    assert success is True
    restored = LeadService.get_lead(db, lead_id)
    assert restored is not None
