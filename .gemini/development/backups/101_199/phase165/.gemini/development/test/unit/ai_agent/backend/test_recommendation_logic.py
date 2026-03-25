import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from db.models import Opportunity, Contact, Model
from ai_agent.backend.recommendations import AIRecommendationService
from web.backend.app.utils.timezone import get_kst_now_naive

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

def test_refresh_temperature_throttling(db: Session):
    unique_id = f"TEST_OPP_{uuid.uuid4().hex[:8]}"
    
    # Ensure clean state
    db.query(Opportunity).filter(Opportunity.id == unique_id).delete()
    db.commit()

    # Setup: Create a test opportunity
    opp = Opportunity(
        id=unique_id,
        name="Test Opportunity",
        stage="Prospecting",
        created_at=get_kst_now_naive() - timedelta(days=1)
    )
    db.add(opp)
    db.commit()

    # 1. Initial refresh - should update
    AIRecommendationService.refresh_opportunity_temperatures(db)
    db.refresh(opp)
    assert opp.updated_by == AIRecommendationService.AI_AGENT_USER
    
    # 2. Immediate second refresh - should be skipped due to throttling
    # Modify temperature manually to see if it gets reverted (it shouldn't if skipped)
    opp.temperature = "Modified Manually"
    db.commit()
    
    AIRecommendationService.refresh_opportunity_temperatures(db)
    db.refresh(opp)
    
    # If skipped, temperature remains "Modified Manually"
    assert opp.temperature == "Modified Manually"
    
    # 3. Simulate "different user" (manually clearing updated_by for test)
    # This should trigger update because author changed
    opp.updated_by = "Human User"
    db.commit()
    
    AIRecommendationService.refresh_opportunity_temperatures(db)
    db.refresh(opp)
    
    # Should update now because updated_by is not 'AI Recommend'
    assert opp.updated_by == AIRecommendationService.AI_AGENT_USER
    assert opp.temperature in ["Hot", "Warm", "Cold"]

    # Cleanup
    db.delete(opp)
    db.commit()
