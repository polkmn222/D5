import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base

# Import all models to ensure test coverage
from db.models import (
    Contact, Lead, Opportunity, Asset, Product, Model, VehicleSpecification,
    MessageSend, MessageTemplate, Task, Attachment
)

# Import services if necessary, or we can test the base mechanism directly
from backend.app.services.contact_service import ContactService
from backend.app.services.lead_service import LeadService
from backend.app.services.opportunity_service import OpportunityService
from backend.app.services.asset_service import AssetService
from backend.app.services.product_service import ProductService
from backend.app.services.model_service import ModelService
from backend.app.services.vehicle_spec_service import VehicleSpecService
from backend.app.services.message_service import MessageService
from backend.app.services.message_template_service import MessageTemplateService

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./.gemini/development/test/databases/test_deletion.db"
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

def test_contact_soft_delete(db):
    """Test that Contact soft deletes and orphaned Opportunities are unaffected."""
    contact = ContactService.create(db, first_name="John", last_name="Doe", email="delete@me.com")
    opp = OpportunityService.create(db, contact=contact.id, name="Test Opp")
    
    assert contact.deleted_at is None
    
    # Perform delete
    ContactService.delete(db, contact.id)
    
    # Refresh objects
    db.refresh(contact)
    db.refresh(opp)
    
    # Assert Contact is soft deleted
    assert contact.deleted_at is not None
    
    # Assert Opportunity is untouched and still points to the soft-deleted Contact
    assert opp.deleted_at is None
    assert opp.contact == contact.id

def test_lead_soft_delete(db):
    lead = LeadService.create(db, first_name="Jane", last_name="Doe")
    LeadService.delete(db, lead.id)
    db.refresh(lead)
    assert lead.deleted_at is not None

def test_product_and_asset_soft_delete(db):
    product = ProductService.create(db, name="Test Vehicle")
    asset = AssetService.create(db, product=product.id, name="Test Asset VIN")
    
    ProductService.delete(db, product.id)
    AssetService.delete(db, asset.id)
    
    db.refresh(product)
    db.refresh(asset)
    
    assert product.deleted_at is not None
    assert asset.deleted_at is not None

def test_vehicle_spec_and_model_soft_delete(db):
    spec = VehicleSpecService.create(db, name="Test Brand")
    model = ModelService.create(db, name="Test Model", brand=spec.id)
    
    VehicleSpecService.delete(db, spec.id)
    ModelService.delete(db, model.id)
    
    db.refresh(spec)
    db.refresh(model)
    
    assert spec.deleted_at is not None
    assert model.deleted_at is not None

def test_messaging_soft_delete(db):
    template = MessageTemplateService.create(db, name="Generic Template")
    msg = MessageService.create(db, template=template.id, content="Hello")
    
    MessageTemplateService.delete(db, template.id)
    MessageService.delete(db, msg.id)
    
    db.refresh(template)
    db.refresh(msg)
    
    assert template.deleted_at is not None
    assert msg.deleted_at is not None

def test_task_soft_delete(db):
    # Testing BaseService directly if no TaskService exists
    from backend.app.services.base_service import BaseService
    
    class TaskService(BaseService[Task]):
        model = Task
        object_name = "Task"
        
    task_obj = TaskService.create(db, subject="Follow Up Tasks")
    TaskService.delete(db, task_obj.id)
    
    db.refresh(task_obj)
    assert task_obj.deleted_at is not None
