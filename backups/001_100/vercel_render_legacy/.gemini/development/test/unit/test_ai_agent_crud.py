import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock, MagicMock

from db.database import Base
from ai_agent.backend.service import AiAgentService
from db.models import Lead, Contact, Opportunity

# Setup Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent_crud.db"
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
async def test_ai_agent_create_lead_conversational(db):
    """Test that the agent handles lead creation requests."""
    # 1. Simulating "I want to create a lead" (Incomplete info)
    mock_llm_response = {
        "intent": "CHAT",
        "text": "Sure! I can help you create a new lead. What is the customer's first and last name?",
        "score": 0.9
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_response
        res = await AiAgentService.process_query(db, "I want to create a lead")
        
        assert res["intent"] == "CHAT"
        assert "first and last name" in res["text"]

    # 2. Simulating "Create lead for Hong Gil-dong, email test@test.com" (Complete info)
    mock_llm_response_complete = {
        "intent": "CREATE",
        "object_type": "lead",
        "data": {
            "first_name": "Gil-dong",
            "last_name": "Hong",
            "email": "test@test.com",
            "status": "New"
        },
        "score": 1.0
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_response_complete
        res = await AiAgentService.process_query(db, "Create lead for Hong Gil-dong, email test@test.com")
        
        assert res["intent"] == "CREATE"
        assert "Success" in res["text"]
        # Check DB
        lead = db.query(Lead).filter(Lead.first_name == "Gil-dong").first()
        assert lead is not None
        assert lead.email == "test@test.com"

@pytest.mark.asyncio
async def test_ai_agent_manage_opportunity(db):
    """Test that the agent can manage (query and then update) an opportunity."""
    # Seed an opportunity
    opp = Opportunity(id="OPP-123", name="Big Deal", amount=1000000, stage="Prospecting")
    db.add(opp)
    db.commit()

    # 1. Simulating "Show me the big deal opportunity"
    mock_llm_query = {
        "intent": "QUERY",
        "object_type": "opportunity",
        "sql": "SELECT * FROM opportunities WHERE name LIKE '%Big Deal%'",
        "score": 0.9
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_query
        res = await AiAgentService.process_query(db, "Show me the big deal opportunity")
        assert len(res["results"]) > 0
        assert res["results"][0]["name"] == "Big Deal"

    # 2. Simulating "Update its amount to 2,000,000"
    mock_llm_update = {
        "intent": "UPDATE",
        "object_type": "opportunity",
        "record_id": "OPP-123",
        "data": {"amount": 2000000},
        "score": 1.0
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_update
        res = await AiAgentService.process_query(db, "Update its amount to 2,000,000")
        assert "Success" in res["text"]
        
        db.refresh(opp)
        assert opp.amount == 2000000

@pytest.mark.asyncio
async def test_ai_agent_korean_support(db):
    """Test that the agent understands Korean queries."""
    mock_llm_korean = {
        "intent": "QUERY",
        "object_type": "contact",
        "text": "고객 목록을 불러왔습니다.",
        "sql": "SELECT * FROM contacts LIMIT 5",
        "score": 0.95
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_korean
        res = await AiAgentService.process_query(db, "고객 목록 보여줘")
        assert res["intent"] == "QUERY"
        assert "고객" in res["text"]
