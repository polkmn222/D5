import pytest
import uuid
from db.database import Base, engine, SessionLocal
from db.models import Contact, Lead, Opportunity, Asset, Product, VehicleSpecification, Model, MessageSend, MessageTemplate
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.asset_service import AssetService
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService
from web.backend.app.services.model_service import ModelService
from web.message.backend.services.message_service import MessageService
from web.message.backend.services.message_template_service import MessageTemplateService

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_contact_crud(db):
    suffix = uuid.uuid4().hex[:6]
    # Create
    contact = ContactService.create_contact(db, first_name="Contact", last_name=f"Tester_{suffix}", email=f"c_{suffix}@example.com")
    assert contact.id is not None
    # Read
    retrieved = ContactService.get_contact(db, contact.id)
    assert retrieved.email == f"c_{suffix}@example.com"
    # Update
    updated = ContactService.update_contact(db, contact.id, phone="123-456-7890")
    assert updated.phone == "123-456-7890"
    # Delete
    success = ContactService.delete_contact(db, contact.id)
    assert success is True
    assert ContactService.get_contact(db, contact.id) is None

def test_lead_crud(db):
    suffix = uuid.uuid4().hex[:6]
    # Create
    lead = LeadService.create_lead(db, first_name="Lead", last_name=f"Tester_{suffix}", email=f"l_{suffix}@example.com")
    assert lead.id is not None
    # Read
    retrieved = LeadService.get_lead(db, lead.id)
    assert retrieved.email == f"l_{suffix}@example.com"
    # Update
    updated = LeadService.update_lead(db, lead.id, status="Follow Up")
    assert updated.status == "Follow Up"
    # Delete
    success = LeadService.delete_lead(db, lead.id)
    assert success is True
    assert LeadService.get_lead(db, lead.id) is None

def test_opportunity_crud(db):
    suffix = uuid.uuid4().hex[:6]
    # Create
    opp = OpportunityService.create_opportunity(db, name=f"Opp_{suffix}", amount=1000)
    assert opp.id is not None
    # Read
    retrieved = OpportunityService.get_opportunity(db, opp.id)
    assert retrieved.name == f"Opp_{suffix}"
    # Update
    updated = OpportunityService.update_opportunity(db, opp.id, amount=2000)
    assert updated.amount == 2000
    # Delete
    success = OpportunityService.delete_opportunity(db, opp.id)
    assert success is True
    assert OpportunityService.get_opportunity(db, opp.id) is None

def test_asset_crud(db):
    suffix = uuid.uuid4().hex[:6]
    # Create
    asset = AssetService.create_asset(db, name=f"Asset_{suffix}", vin=f"VIN_{suffix}")
    assert asset.id is not None
    # Read
    retrieved = AssetService.get_asset(db, asset.id)
    assert retrieved.vin == f"VIN_{suffix}"
    # Update
    updated = AssetService.update_asset(db, asset.id, status="Inactive")
    assert updated.status == "Inactive"
    # Delete
    success = AssetService.delete_asset(db, asset.id)
    assert success is True
    assert AssetService.get_asset(db, asset.id) is None

def test_product_crud(db):
    suffix = uuid.uuid4().hex[:6]
    # Create
    product = ProductService.create_product(db, name=f"Product_{suffix}", base_price=500)
    assert product.id is not None
    # Read
    retrieved = ProductService.get_product(db, product.id)
    assert retrieved.name == f"Product_{suffix}"
    # Update
    updated = ProductService.update_product(db, product.id, base_price=600)
    assert updated.base_price == 600
    # Delete
    success = ProductService.delete_product(db, product.id)
    assert success is True
    assert ProductService.get_product(db, product.id) is None

def test_vehicle_spec_crud(db):
    suffix = uuid.uuid4().hex[:6]
    # Create
    spec = VehicleSpecService.create_spec(db, name=f"Spec_{suffix}", record_type="Brand")
    assert spec.id is not None
    # Read
    retrieved = VehicleSpecService.get_vehicle_spec(db, spec.id)
    assert retrieved.name == f"Spec_{suffix}"
    # Update
    # VehicleSpecService doesn't have an update_spec method in the file I saw? 
    # Let me check again. It only had create, get, list, delete.
    # Ah, I should use the BaseService update if it inherits, but it doesn't seem to inherit BaseService.
    # Actually, I'll just skip update for now or check if I can use a generic update.
    # Wait, Step 139 showed VehicleSpecService: only create, get_vehicle_specs, get_vehicle_spec, delete_vehicle_spec.
    # So I'll remove the update part for spec.
    
    # Delete
    success = VehicleSpecService.delete_vehicle_spec(db, spec.id)
    assert success is True
    assert VehicleSpecService.get_vehicle_spec(db, spec.id) is None

def test_model_crud(db):
    suffix = uuid.uuid4().hex[:6]
    # Create
    model = ModelService.create_model(db, name=f"Model_{suffix}")
    assert model.id is not None
    # Read
    retrieved = ModelService.get_model(db, model.id)
    assert retrieved.name == f"Model_{suffix}"
    # Update
    updated = ModelService.update_model(db, model.id, description="Model Description")
    assert updated.description == "Model Description"
    # Delete
    success = ModelService.delete_model(db, model.id)
    assert success is True
    assert ModelService.get_model(db, model.id) is None

def test_message_send_crud(db):
    suffix = uuid.uuid4().hex[:6]
    # Need a valid contact for foreign key validation
    contact = ContactService.create_contact(db, first_name="Msg", last_name="Contact")
    # Create
    msg = MessageService.create_message(db, contact=contact.id, content=f"Hello_{suffix}", direction="Outbound")
    assert msg.id is not None
    # Read
    retrieved = MessageService.get_message(db, msg.id)
    assert retrieved.content == f"Hello_{suffix}"
    # Update
    updated = MessageService.update_message(db, msg.id, status="SENT")
    assert updated.status == "SENT"
    # Delete
    success = MessageService.delete_message(db, msg.id)
    assert success is True
    assert MessageService.get_message(db, msg.id) is None
    # Clean up contact
    ContactService.delete_contact(db, contact.id)

def test_message_template_crud(db):
    suffix = uuid.uuid4().hex[:6]
    # Create
    tpl = MessageTemplateService.create_template(db, name=f"Tpl_{suffix}", content="Welcome!")
    assert tpl.id is not None
    # Read
    retrieved = MessageTemplateService.get_template(db, tpl.id)
    assert retrieved.name == f"Tpl_{suffix}"
    # Update
    updated = MessageTemplateService.update_template(db, tpl.id, subject="Hello")
    assert updated.subject == "Hello"
    # Delete
    success = MessageTemplateService.delete_template(db, tpl.id)
    assert success is True
    assert MessageTemplateService.get_template(db, tpl.id) is None
