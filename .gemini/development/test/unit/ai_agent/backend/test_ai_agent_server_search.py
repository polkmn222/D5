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
async def test_server_side_search_sql_generation(db: Session):
    """Verify that a search query generates SQL with ILIKE clauses."""
    # This specifically tests the robust extraction and _apply_search_to_sql
    query = "search leads for John"
    response = await AiAgentService.process_query(db, query)
    
    assert response["intent"] == "QUERY"
    assert response["object_type"] == "lead"
    assert "sql" in response
    # The SQL should contain ILIKE and the search term
    sql = response["sql"].lower()
    assert "ilike" in sql
    assert "%john%" in sql
    # It should search across multiple fields as defined in search_fields
    assert "first_name" in sql or "last_name" in sql or "email" in sql

@pytest.mark.asyncio
async def test_search_no_results_pagination(db: Session):
    """Verify that search returns a valid pagination object even with no results."""
    query = "search leads for NonExistentRecord123456"
    response = await AiAgentService.process_query(db, query)
    
    assert response["intent"] == "QUERY"
    assert "pagination" in response
    assert response["pagination"]["total"] == 0
    assert response["results"] == []
