import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

from db.database import Base, engine, SessionLocal
from ai_agent.backend.service import AiAgentService
from db.models import Lead, Contact, Opportunity

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.mark.asyncio
async def test_ai_agent_create_lead_conversational(db):
    """Test that the agent handles lead creation requests."""
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"test-{unique_id}@test.com"
    test_first_name = f"Gil-dong-{unique_id}"

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
            "first_name": test_first_name,
            "last_name": "Hong",
            "email": test_email,
            "status": "New"
        },
        "score": 1.0
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_response_complete
        res = await AiAgentService.process_query(db, f"Create lead for Hong {test_first_name}, email {test_email}")
        
        assert res["intent"] == "CREATE"
        assert "Success" in res["text"]
        # Check DB
        lead = db.query(Lead).filter(Lead.first_name == test_first_name).first()
        assert lead is not None
        assert lead.email == test_email

@pytest.mark.asyncio
async def test_ai_agent_manage_opportunity(db):
    """Test that the agent can manage (query and then update) an opportunity."""
    unique_id = uuid.uuid4().hex[:8]
    test_opp_id = f"OPP-{unique_id}"
    test_opp_name = f"Big Deal-{unique_id}"

    # Seed an opportunity
    opp = Opportunity(id=test_opp_id, name=test_opp_name, amount=1000000, stage="Prospecting")
    db.add(opp)
    db.commit()

    # 1. Simulating "Show me the big deal opportunity"
    mock_llm_query = {
        "intent": "QUERY",
        "object_type": "opportunity",
        "sql": f"SELECT * FROM opportunities WHERE name LIKE '%{test_opp_name}%'",
        "score": 0.9
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_query
        res = await AiAgentService.process_query(db, f"Show me the {test_opp_name} opportunity")
        assert len(res["results"]) > 0
        assert res["results"][0]["name"] == test_opp_name

    # 2. Simulating "Update its amount to 2,000,000"
    mock_llm_update = {
        "intent": "UPDATE",
        "object_type": "opportunity",
        "record_id": test_opp_id,
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
