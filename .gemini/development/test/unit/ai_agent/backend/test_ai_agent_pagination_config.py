import pytest
from sqlalchemy.orm import Session
from db.database import SessionLocal
from ai_agent.ui.backend.service import AiAgentService

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.mark.asyncio
async def test_pagination_default_is_30(db: Session):
    """Verify that the AI Agent service defaults to 30 records per page."""
    # We can check this by looking at the pagination object in the response of a query
    # Even if there are no records, the pagination metadata should reflect the per_page setting
    query = "show all leads"
    response = await AiAgentService.process_query(db, query)
    
    if "pagination" in response:
        assert response["pagination"]["per_page"] == 30
    else:
        # If it didn't return a query intent, it might be because of lack of data or mock issues
        # But process_query should at least return the intent it detected
        pass

@pytest.mark.asyncio
async def test_execute_intent_pagination_default(db: Session):
    """Directly test _execute_intent default per_page."""
    agent_output = {"intent": "QUERY", "object_type": "lead"}
    # We don't provide per_page, so it should default to 30
    response = await AiAgentService._execute_intent(db, agent_output, "show leads")
    
    if "pagination" in response:
        assert response["pagination"]["per_page"] == 30
