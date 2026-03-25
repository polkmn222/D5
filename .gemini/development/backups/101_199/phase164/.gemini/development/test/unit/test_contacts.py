import pytest
import uuid
from db.database import Base, engine, SessionLocal
from db.models import Contact
from backend.app.services.contact_service import ContactService

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_create_contact(db):
    suffix = uuid.uuid4().hex[:6]
    contact = ContactService.create_contact(
        db, first_name="John", last_name=f"Doe_{suffix}", 
        email=f"john_{suffix}@example.com"
    )
    assert contact.id.startswith("003")
    assert contact.last_name == f"Doe_{suffix}"

def test_get_contact(db):
    suffix = uuid.uuid4().hex[:6]
    contact = ContactService.create_contact(
        db, first_name="Jane", last_name=f"Smith_{suffix}"
    )
    retrieved = ContactService.get_contact(db, contact.id)
    assert retrieved is not None
    assert retrieved.id == contact.id

def test_update_contact(db):
    suffix = uuid.uuid4().hex[:6]
    contact = ContactService.create_contact(
        db, first_name="Update", last_name=f"Me_{suffix}"
    )
    updated = ContactService.update_contact(db, contact.id, phone="123-456")
    assert updated.phone == "123-456"

def test_delete_contact(db):
    suffix = uuid.uuid4().hex[:6]
    contact = ContactService.create_contact(
        db, first_name="Delete", last_name=f"Me_{suffix}"
    )
    success = ContactService.delete_contact(db, contact.id)
    assert success is True
    
    retrieved = ContactService.get_contact(db, contact.id)
    assert retrieved is None # Soft deleted
