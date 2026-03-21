import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

from db.database import Base
from ai_agent.backend.service import AiAgentService
from db.models import Lead

# Setup Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./db/test_runs/test_ai_lead_debug.db"
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

@pytest.mark.asyncio
async def test_debug_lead_creation_flow(db):
    """Debug the full conversational lead creation flow."""
    
    # User: "리드 만들어줘 박상열, test@test.com, 01012345678"
    # Agent should ask for status because it's mandatory but missing in user intent or data usually.
    # Actually, let's see what happens if we provide status.
    
    mock_complete_lead = {
        "intent": "CREATE",
        "object_type": "lead",
        "data": {
            "last_name": "박상열",
            "email": "test@test.com",
            "phone": "01012345678",
            "status": "New"
        },
        "text": "박상열 리드를 생성합니다.",
        "score": 1.0
    }

    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_complete_lead
        
        # This simulates the final step where user gave the status
        res = await AiAgentService.process_query(db, "new")
        
        print(f"Agent Response: {res}")
        assert res["intent"] == "CREATE"
        assert "Success" in res["text"]
        
        # Check DB
        lead = db.query(Lead).filter(Lead.last_name == "박상열").first()
        assert lead is not None
        assert lead.status == "New"

@pytest.mark.asyncio
async def test_debug_recent_lead_query(db):
    """Debug querying the lead that was just created."""
    # Seed a lead
    lead = Lead(id="00Q-test", last_name="박상열", status="New")
    db.add(lead)
    db.commit()
    
    mock_query_response = {
        "intent": "QUERY",
        "object_type": "lead",
        "sql": "SELECT id, last_name, status FROM leads WHERE last_name = '박상열' ORDER BY created_at DESC LIMIT 1",
        "text": "박상열님의 리드 정보를 찾았습니다.",
        "score": 1.0
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_response
        res = await AiAgentService.process_query(db, "방금 생성된 리드 조회해줘")
        
        assert "results" in res
        assert len(res["results"]) > 0
        assert res["results"][0]["last_name"] == "박상열"
