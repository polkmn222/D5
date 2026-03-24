import pytest
import uuid
from unittest.mock import patch, AsyncMock
from db.database import Base, engine, SessionLocal
from ai_agent.backend.service import AiAgentService
from db.models import Contact, Opportunity

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.mark.asyncio
async def test_ai_contact_crud_flow(db):
    """Test full CRUD lifecycle for Contact via AI Agent."""
    unique_id = uuid.uuid4().hex[:8]
    test_last_name = f"Kim-{unique_id}"
    test_email = f"kim-{unique_id}@test.com"
    
    # 1. CREATE
    mock_create = {
        "intent": "CREATE",
        "object_type": "contact",
        "data": {"last_name": test_last_name, "first_name": "Chul-su", "email": test_email},
        "text": f"Creating contact {test_last_name} Chul-su.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_create
        res = await AiAgentService.process_query(db, f"Create contact last_name {test_last_name} first_name Chul-su email {test_email}")
        assert "Success" in res["text"]
        contact = db.query(Contact).filter(Contact.last_name == test_last_name).first()
        assert contact is not None
        contact_id = contact.id

    # 2. READ (QUERY)
    mock_query = {
        "intent": "QUERY",
        "object_type": "contact",
        "sql": f"SELECT * FROM contacts WHERE id = '{contact_id}'",
        "text": "Found the contact.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query
        res = await AiAgentService.process_query(db, f"Find contact {test_last_name}")
        assert len(res["results"]) > 0
        assert res["results"][0]["last_name"] == test_last_name

    # 3. UPDATE
    mock_update = {
        "intent": "UPDATE",
        "object_type": "contact",
        "record_id": contact_id,
        "data": {"phone": "010-5555-5555"},
        "text": "Updating contact phone.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_update
        res = await AiAgentService.process_query(db, f"Update contact {contact_id} phone to 010-5555-5555")
        assert "Success" in res["text"]
        db.refresh(contact)
        assert contact.phone == "010-5555-5555"

    # 4. DELETE
    mock_delete = {
        "intent": "DELETE",
        "object_type": "contact",
        "record_id": contact_id,
        "text": "Deleting contact.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_delete
        res = await AiAgentService.process_query(db, f"Delete contact {contact_id}")
        assert "Success" in res["text"]
        deleted = db.query(Contact).filter(Contact.id == contact_id).first()
        assert deleted is not None
        assert deleted.deleted_at is not None # Verify soft delete

@pytest.mark.asyncio
async def test_ai_opportunity_crud_flow(db):
    """Test full CRUD lifecycle for Opportunity via AI Agent."""
    unique_id = uuid.uuid4().hex[:8]
    test_opp_name = f"Solar-{unique_id}"
    
    # 1. CREATE
    mock_create = {
        "intent": "CREATE",
        "object_type": "opportunity",
        "data": {"name": test_opp_name, "amount": 5000000, "stage": "Prospecting"},
        "text": "Creating opportunity.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_create
        res = await AiAgentService.process_query(db, f"Create opportunity name {test_opp_name} amount 5000000 stage Prospecting")
        assert "Success" in res["text"]
        opp = db.query(Opportunity).filter(Opportunity.name == test_opp_name).first()
        assert opp is not None
        opp_id = opp.id

    # 2. READ
    mock_query = {
        "intent": "QUERY",
        "object_type": "opportunity",
        "sql": f"SELECT * FROM opportunities WHERE id = '{opp_id}'",
        "text": "Found it.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query
        res = await AiAgentService.process_query(db, f"Show me {test_opp_name}")
        assert res["results"][0]["name"] == test_opp_name

    # 3. UPDATE
    mock_update = {
        "intent": "UPDATE",
        "object_type": "opportunity",
        "record_id": opp_id,
        "data": {"stage": "Value Proposition"},
        "text": "Updating stage.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_update
        res = await AiAgentService.process_query(db, f"Update opp {opp_id} stage to Value Proposition")
        assert "Success" in res["text"]
        db.refresh(opp)
        assert opp.stage == "Value Proposition"

    # 4. DELETE
    mock_delete = {
        "intent": "DELETE",
        "object_type": "opportunity",
        "record_id": opp_id,
        "text": "Deleting opportunity.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_delete
        res = await AiAgentService.process_query(db, f"Delete opportunity {opp_id}")
        assert "Success" in res["text"]
        deleted = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        assert deleted is not None
        assert deleted.deleted_at is not None # Verify soft delete
