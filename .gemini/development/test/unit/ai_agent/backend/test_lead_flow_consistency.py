"""
Phase 169: Lead flow consistency unit tests.
Tests use _execute_intent directly to avoid LLM non-determinism.
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import Lead
from ai_agent.ui.backend.service import AiAgentService

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.mark.asyncio
async def test_lead_create_returns_view_card(db: Session):
    """Verify that creating a lead via _execute_intent returns a chat_card in view mode.
    
    Uses _execute_intent directly to avoid LLM non-determinism.
    """
    agent_output = {
        "intent": "CREATE",
        "object_type": "lead",
        "data": {"first_name": "John", "last_name": "Doe", "status": "New", "email": "john@example.com"},
        "language_preference": None,
        "score": 1.0,
    }

    with patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.clear_pending_create"), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_created"), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_object"):
        response = await AiAgentService._execute_intent(db, agent_output, "create lead John Doe status New email john@example.com")

    assert response["intent"] == "OPEN_RECORD"
    assert "chat_card" in response
    assert response["chat_card"]["mode"] == "view"
    assert "Doe" in response["chat_card"]["title"]

    # Cleanup
    record_id = response["chat_card"]["record_id"]
    db.query(Lead).filter(Lead.id == record_id).delete()
    db.commit()

@pytest.mark.asyncio
async def test_lead_update_returns_view_card(db: Session):
    """Verify that updating a lead via _execute_intent returns a chat_card in view mode."""
    # Ensure cleanup from any previous runs
    db.query(Lead).filter(Lead.id == "TEST_FLOW_LEAD").delete()
    db.commit()

    # Setup
    lead = Lead(id="TEST_FLOW_LEAD", first_name="Flow", last_name="Test", status="New")
    db.add(lead)
    db.commit()

    agent_output = {
        "intent": "UPDATE",
        "object_type": "lead",
        "record_id": "TEST_FLOW_LEAD",
        "data": {"status": "Qualified"},
        "language_preference": None,
        "score": 1.0,
    }

    with patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_object"):
        response = await AiAgentService._execute_intent(
            db, agent_output, "update lead TEST_FLOW_LEAD status Qualified"
        )

    assert response["intent"] == "OPEN_RECORD"
    assert "chat_card" in response
    assert response["chat_card"]["mode"] == "view"

    # Cleanup
    lead_to_delete = db.query(Lead).filter(Lead.id == "TEST_FLOW_LEAD").first()
    if lead_to_delete:
        db.delete(lead_to_delete)
        db.commit()
