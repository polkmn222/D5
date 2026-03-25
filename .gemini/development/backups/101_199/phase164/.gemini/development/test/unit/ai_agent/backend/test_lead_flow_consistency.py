import pytest
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import Lead
from ai_agent.backend.service import AiAgentService

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.mark.asyncio
async def test_lead_create_returns_view_card(db: Session):
    """Verify that creating a lead via AI Agent returns a chat_card in view mode."""
    query = "create lead for John Doe status New email john@example.com"
    response = await AiAgentService.process_query(db, query)
    
    assert response["intent"] == "CREATE"
    assert "chat_card" in response
    assert response["chat_card"]["mode"] == "view"
    assert "John Doe" in response["chat_card"]["title"]
    
    # Cleanup
    db.query(Lead).filter(Lead.id == response["chat_card"]["record_id"]).delete()
    db.commit()

@pytest.mark.asyncio
async def test_lead_update_returns_view_card(db: Session):
    """Verify that updating a lead via AI Agent returns a chat_card in view mode."""
    # Setup
    lead = Lead(id="TEST_FLOW_LEAD", first_name="Flow", last_name="Test", status="New")
    db.add(lead)
    db.commit()
    
    query = "update lead TEST_FLOW_LEAD status Qualified"
    response = await AiAgentService.process_query(db, query)
    
    assert response["intent"] == "UPDATE" or response["intent"] == "MANAGE" # MANAGE is returned for Lead updates in our implementation
    assert "chat_card" in response
    assert response["chat_card"]["mode"] == "view"
    
    # Cleanup
    db.delete(lead)
    db.commit()
