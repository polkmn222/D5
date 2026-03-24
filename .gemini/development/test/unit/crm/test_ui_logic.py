import pytest
from unittest.mock import MagicMock
from fastapi import Request
from db.database import SessionLocal, Base, engine
from db.models import Contact, Lead, Opportunity, Asset
from web.backend.app.api.routers.contact_router import contact_detail, batch_save_contact
from web.backend.app.api.routers.lead_router import lead_detail
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.asset_service import AssetService

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.mark.asyncio
async def test_contact_detail_context(db):
    # Create contact and related data
    contact = ContactService.create_contact(db, first_name="Detail", last_name="Tester", email="detail@example.com")
    opp = OpportunityService.create_opportunity(db, name="Related Opp", contact=contact.id)
    asset = AssetService.create_asset(db, name="Related Asset", contact=contact.id)
    
    request = MagicMock(spec=Request)
    
    # We call the router function directly
    # Note: Need to mock 'Depends(get_db)' behavior if calling directly, but here we pass 'db' explicitly
    response = await contact_detail(request, contact.id, db)
    
    # If response is a TemplateResponse, we can check its context
    assert response.template.name == "contacts/detail_view.html"
    context = response.context
    assert context["record_id"] == contact.id
    assert context["details"]["Email"] == "detail@example.com"
    
    # Check related lists
    related_titles = [rl["title"] for rl in context["related_lists"]]
    assert "Opportunities" in related_titles
    assert "Assets" in related_titles
    
    # Clean up
    OpportunityService.delete_opportunity(db, opp.id)
    AssetService.delete_asset(db, asset.id)
    ContactService.delete_contact(db, contact.id)

@pytest.mark.asyncio
async def test_contact_inline_edit(db):
    contact = ContactService.create_contact(db, first_name="Inline", last_name="Edit")
    updates = {"First Name": "NewName", "Tier": "Gold"}
    
    # Call batch_save_contact
    response = await batch_save_contact(contact.id, updates, db)
    assert response["status"] == "success"
    
    db.refresh(contact)
    assert contact.first_name == "NewName"
    assert contact.tier == "Gold"
    
    # Clean up
    ContactService.delete_contact(db, contact.id)

@pytest.mark.asyncio
async def test_lead_detail_context(db):
    lead = LeadService.create_lead(db, first_name="Lead", last_name="Detail")
    request = MagicMock(spec=Request)
    
    # Similar to contact_detail
    response = await lead_detail(request, lead.id, db)
    assert response.template.name == "leads/detail_view.html"
    assert response.context["record_id"] == lead.id
    
    # Clean up
    LeadService.delete_lead(db, lead.id)
