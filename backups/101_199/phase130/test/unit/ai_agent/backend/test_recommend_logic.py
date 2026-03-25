import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from unittest.mock import patch, AsyncMock
import uuid

from db.database import Base, engine, SessionLocal
from ai_agent.backend.service import AiAgentService
from ai_agent.backend.recommendations import AIRecommendationService
from db.models import Opportunity, Contact

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.mark.asyncio
async def test_change_recommend_logic_flow(db):
    """Test the conversational flow for changing AI recommendation logic."""
    
    # 1. User asks to change logic without specific mode
    mock_query_ask = {
        "intent": "MODIFY_UI",
        "object_type": None,
        "text": "Change AI Recommend Table",
        "score": 1.0
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_ask
        res = await AiAgentService.process_query(db, "Change AI Recommend Table")
        
        # Should ask which logic to apply
        assert "current **AI Recommend** logic" in res["text"]
        assert "[Hot Deals" in res["text"]

    # 2. User selects "Follow Up"
    mock_query_select = {
        "intent": "MODIFY_UI",
        "object_type": None,
        "text": "Set to Follow Up",
        "score": 1.0
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_select
        res = await AiAgentService.process_query(db, "Follow Up")
        
        assert "Follow Up" in res["text"]
        assert AIRecommendationService.CURRENT_MODE == "Follow Up"

@pytest.mark.asyncio
async def test_recommendation_filtering_logic(db):
    """Test if the filtering logic actually works for different modes."""
    from db.models import VehicleSpecification, Model
    # Seed data
    suffix = uuid.uuid4().hex[:6]
    
    brand = VehicleSpecification(id=f"avS_b_{suffix}", name="Test Brand", record_type="Brand")
    db.add(brand)
    db.flush() # Ensure brand exists for FK
    
    model = Model(id=f"avS_m_{suffix}", name="Test Model", brand=brand.id)
    contact = Contact(id=f"003_{suffix}", last_name="Tester", email="t@t.com")
    db.add(model)
    db.add(contact)
    db.flush()
    
    # Hot deal (Test Drive)
    opp_hot = Opportunity(
        id=f"006_hot_{suffix}", 
        name="Hot Opp", 
        contact=contact.id, 
        model=model.id,
        stage="Test Drive", 
        amount=1000
    )
    opp_hot.created_at = datetime.now()
    
    # Follow-up deal
    opp_follow = Opportunity(
        id=f"006_follow_{suffix}", 
        name="Follow Opp", 
        contact=contact.id, 
        model=model.id,
        stage="Prospecting", 
        amount=10000
    )
    opp_follow.is_followed = True
    opp_won = Opportunity(
        id=f"006_won_{suffix}",
        name="Won Opp",
        contact=contact.id,
        model=model.id,
        stage="Closed Won",
        amount=5000,
    )
    opp_old_hot = Opportunity(
        id=f"006_old_hot_{suffix}",
        name="Old Hot Opp",
        contact=contact.id,
        model=model.id,
        stage="Test Drive",
        amount=2000,
    )
    opp_old_won = Opportunity(
        id=f"006_old_won_{suffix}",
        name="Old Won Opp",
        contact=contact.id,
        model=model.id,
        stage="Closed Won",
        amount=4000,
    )
    db.add(opp_hot)
    db.add(opp_follow)
    db.add(opp_won)
    db.add(opp_old_hot)
    db.add(opp_old_won)
    db.commit()
    baseline = datetime.now()
    opp_hot.created_at = baseline
    opp_follow.created_at = baseline
    opp_follow.updated_at = baseline + timedelta(days=1)
    opp_won.created_at = baseline
    opp_won.updated_at = baseline + timedelta(days=2)
    opp_old_hot.created_at = baseline - timedelta(days=8)
    opp_old_won.created_at = baseline - timedelta(days=8)
    opp_old_won.updated_at = baseline - timedelta(days=8)
    db.commit()

    # Test Hot Deals mode
    AIRecommendationService.set_recommendation_mode("Hot Deals")
    recommends = AIRecommendationService.get_ai_recommendations(db)
    assert any(o.id == opp_hot.id for o in recommends)
    assert not any(o.id == opp_follow.id for o in recommends)
    assert not any(o.id == opp_old_hot.id for o in recommends)

    # Test Follow Up mode
    AIRecommendationService.set_recommendation_mode("Follow Up")
    recommends = AIRecommendationService.get_ai_recommendations(db, limit=100)
    assert any(o.id == opp_follow.id for o in recommends)
    assert not any(o.id == opp_hot.id for o in recommends)
    assert not any(o.id == opp_won.id for o in recommends)

    # Test Closed Won mode
    AIRecommendationService.set_recommendation_mode("Closing Soon")
    recommends = AIRecommendationService.get_ai_recommendations(db, limit=100)
    assert any(o.id == opp_won.id for o in recommends)
    assert not any(o.id == opp_hot.id for o in recommends)
    assert not any(o.id == opp_old_won.id for o in recommends)

    # Test New Records excludes won/lost
    AIRecommendationService.set_recommendation_mode("Default")
    recommends = AIRecommendationService.get_ai_recommendations(db, limit=100)
    assert any(o.id == opp_hot.id for o in recommends)
    assert any(o.id == opp_follow.id for o in recommends)
    assert not any(o.id == opp_won.id for o in recommends)
    assert not any(o.id == opp_old_hot.id for o in recommends)
