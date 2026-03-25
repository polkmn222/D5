import pytest
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
        assert "How should I filter" in res["text"]
        assert "[Hot Deals]" in res["text"]

    # 2. User selects "High Value"
    mock_query_select = {
        "intent": "MODIFY_UI",
        "object_type": None,
        "text": "Set to High Value",
        "score": 1.0
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_select
        res = await AiAgentService.process_query(db, "High Value")
        
        assert "High Value" in res["text"]
        assert AIRecommendationService.CURRENT_MODE == "High Value"

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
    
    # High value deal
    opp_high = Opportunity(
        id=f"006_high_{suffix}", 
        name="High Opp", 
        contact=contact.id, 
        model=model.id,
        stage="Prospecting", 
        amount=60000000 # 60M
    )
    
    db.add(opp_hot)
    db.add(opp_high)
    db.commit()

    # Test Hot Deals mode
    AIRecommendationService.set_recommendation_mode("Hot Deals")
    recommends = AIRecommendationService.get_ai_recommendations(db)
    assert any(o.id == opp_hot.id for o in recommends)
    assert not any(o.id == opp_high.id for o in recommends)

    # Test High Value mode
    AIRecommendationService.set_recommendation_mode("High Value")
    recommends = AIRecommendationService.get_ai_recommendations(db, limit=100)
    assert any(o.id == opp_high.id for o in recommends)
    assert not any(o.id == opp_hot.id for o in recommends)
