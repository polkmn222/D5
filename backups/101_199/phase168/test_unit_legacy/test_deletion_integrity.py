import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, engine, SessionLocal

# Import all models to ensure test coverage
from db.models import (
    Contact, Lead, Opportunity, Asset, Product, Model, VehicleSpecification,
    MessageSend, MessageTemplate, Attachment
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

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_contact_soft_delete(db):
    """Test that Contact soft deletes and orphaned Opportunities are unaffected."""
    unique_id = uuid.uuid4().hex[:8]
    contact = ContactService.create(db, first_name="John", last_name=f"Doe-{unique_id}", email=f"delete-{unique_id}@me.com")
    opp = OpportunityService.create(db, contact=contact.id, name=f"Test Opp-{unique_id}")
    
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
    unique_id = uuid.uuid4().hex[:8]
    lead = LeadService.create(db, first_name="Jane", last_name=f"Doe-{unique_id}")
    LeadService.delete(db, lead.id)
    db.refresh(lead)
    assert lead.deleted_at is not None

def test_product_and_asset_soft_delete(db):
    unique_id = uuid.uuid4().hex[:8]
    product = ProductService.create(db, name=f"Test Vehicle-{unique_id}")
    asset = AssetService.create(db, product=product.id, name=f"Test Asset VIN-{unique_id}")
    
    ProductService.delete(db, product.id)
    AssetService.delete(db, asset.id)
    
    db.refresh(product)
    db.refresh(asset)
    
    assert product.deleted_at is not None
    assert asset.deleted_at is not None

def test_vehicle_spec_and_model_soft_delete(db):
    unique_id = uuid.uuid4().hex[:8]
    spec = VehicleSpecService.create(db, name=f"Test Brand-{unique_id}")
    model = ModelService.create(db, name=f"Test Model-{unique_id}", brand=spec.id)
    
    VehicleSpecService.delete(db, spec.id)
    ModelService.delete(db, model.id)
    
    db.refresh(spec)
    db.refresh(model)
    
    assert spec.deleted_at is not None
    assert model.deleted_at is not None

def test_messaging_soft_delete(db):
    unique_id = uuid.uuid4().hex[:8]
    template = MessageTemplateService.create(db, name=f"Generic Template-{unique_id}")
    msg = MessageService.create(db, template=template.id, content="Hello")
    
    MessageTemplateService.delete(db, template.id)
    MessageService.delete(db, msg.id)
    
    db.refresh(template)
    db.refresh(msg)
    
    assert template.deleted_at is not None
    assert msg.deleted_at is not None
