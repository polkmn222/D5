import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from backend.app.services.contact_service import ContactService

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./db/test_runs/test_crm.db"
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

def test_create_contact(db):
    contact = ContactService.create_contact(
        db, 
        first_name="John", 
        last_name="Doe", 
        email="john@example.com", 
        phone="010-1234-5678",
        status="New",
        description="Test Lead"
    )
    assert contact.id is not None
    assert contact.first_name == "John"
    assert contact.email == "john@example.com"

def test_get_contact(db):
    created = ContactService.create_contact(db, first_name="Jane", last_name="Smith", email="jane@example.com", phone="010-9999-9999")
    fetched = ContactService.get_contact(db, created.id)
    assert fetched.id == created.id
    assert fetched.last_name == "Smith"

def test_update_contact(db):
    contact = ContactService.create_contact(db, first_name="Update", last_name="Me", email="update@example.com", phone="010-0000-0000")
    updated = ContactService.update_contact(db, contact.id, status="Qualified", description="Hot lead")
    assert updated.status == "Qualified"
    assert updated.description == "Hot lead"

def test_delete_contact(db):
    contact = ContactService.create_contact(db, first_name="Delete", last_name="Me", email="delete@example.com", phone="010-1111-1111")
    success = ContactService.delete_contact(db, contact.id)
    assert success is True
    assert ContactService.get_contact(db, contact.id) is None
