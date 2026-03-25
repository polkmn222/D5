import pytest
import uuid
from unittest.mock import patch, AsyncMock
from db.database import Base, engine, SessionLocal
from ai_agent.backend.service import AiAgentService
from db.models import Lead

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.mark.asyncio
async def test_debug_lead_creation_flow(db):
    """Debug the full conversational lead creation flow."""
    unique_id = uuid.uuid4().hex[:8]
    test_last_name = f"박상열-{unique_id}"
    test_email = f"test-{unique_id}@test.com"
    
    mock_complete_lead = {
        "intent": "CREATE",
        "object_type": "lead",
        "data": {
            "last_name": test_last_name,
            "email": test_email,
            "phone": "01012345678",
            "status": "New"
        },
        "text": f"{test_last_name} 리드를 생성합니다.",
        "score": 1.0
    }

    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_complete_lead
        res = await AiAgentService.process_query(db, f"리드 만들어줘 {test_last_name}, {test_email}, 01012345678")
        
        assert res["intent"] == "CREATE"
        # Check if actually created
        lead = db.query(Lead).filter(Lead.last_name == test_last_name).first()
        assert lead is not None
        assert lead.email == test_email
