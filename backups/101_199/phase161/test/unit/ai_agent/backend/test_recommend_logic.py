import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from db.database import SessionLocal, Base, engine
from db.models import Opportunity, Contact, Model, VehicleSpecification
from ai_agent.backend.recommendations import AIRecommendationService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService
from web.backend.app.utils.timezone import get_kst_now_naive

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

def test_refresh_opportunity_temperatures(db):
    # Setup: Create opportunities with different stages
    opp_hot = OpportunityService.create_opportunity(db, name="Hot Opp", stage="Test Drive")
    opp_cold = OpportunityService.create_opportunity(db, name="Cold Opp", stage="Closed Lost")
    
    # Run refresh - Mock _already_refreshed_today to force refresh
    with patch.object(AIRecommendationService, '_already_refreshed_today', return_value=False):
        AIRecommendationService.refresh_opportunity_temperatures(db)
    
    db.refresh(opp_hot)
    db.refresh(opp_cold)
    
    assert opp_hot.temperature == "Hot"
    assert opp_cold.temperature == "Cold"
    
    # Clean up
    OpportunityService.delete_opportunity(db, opp_hot.id)
    OpportunityService.delete_opportunity(db, opp_cold.id)

def test_get_ai_recommendations_hot_deals(db):
    # Setup: Create contact, model, and opportunities
    contact = ContactService.create_contact(db, first_name="Rec", last_name="Tester", phone="010-1234-5678")
    brand = VehicleSpecService.create_spec(db, name="Test Brand", record_type="Brand")
    model = ModelService.create_model(db, name="Test Model", brand=brand.id)
    
    # Hot deal: Stage="Test Drive" AND created within 7 days
    opp = OpportunityService.create_opportunity(
        db, name="Hot Deal Opp", contact=contact.id, model=model.id, stage="Test Drive"
    )
    
    # Run recommendation
    recommendations = AIRecommendationService.get_ai_recommendations(db, mode="Hot Deals")
    
    assert any(o.id == opp.id for o in recommendations)
    
    # Clean up
    OpportunityService.delete_opportunity(db, opp.id)
    ModelService.delete_model(db, model.id)
    VehicleSpecService.delete_vehicle_spec(db, brand.id)
    ContactService.delete_contact(db, contact.id)

def test_get_sendable_recommendations(db):
    # Setup: Create contact with phone and model
    contact = ContactService.create_contact(db, first_name="Sendable", last_name="Tester", phone="010-9999-9999")
    brand = VehicleSpecService.create_spec(db, name="Brand2", record_type="Brand")
    model = ModelService.create_model(db, name="Model2", brand=brand.id)
    
    opp = OpportunityService.create_opportunity(
        db, name="Sendable Opp", contact=contact.id, model=model.id, stage="Test Drive"
    )
    
    # Run sendable check
    sendable = AIRecommendationService.get_sendable_recommendations(db)
    
    assert any(o.id == opp.id for o in sendable)
    
    # Clean up
    OpportunityService.delete_opportunity(db, opp.id)
    ModelService.delete_model(db, model.id)
    VehicleSpecService.delete_vehicle_spec(db, brand.id)
    ContactService.delete_contact(db, contact.id)
