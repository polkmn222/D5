import pytest
from unittest.mock import patch, MagicMock
from db.models import Lead
from ai_agent.ui.backend.service import AiAgentService

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.mark.asyncio
async def test_manage_lead_intent_returns_correct_card_and_record_id(mock_db):
    mock_lead = Lead(id="123", first_name="Test", last_name="Lead", status="New")
    
    with patch("ai_agent.ui.backend.service.LeadService.get_lead", return_value=mock_lead):
        with patch("ai_agent.ui.backend.service.AiAgentService._call_multi_llm_ensemble", return_value={"intent": "MANAGE", "object_type": "lead", "record_id": "123"}):
            with patch("ai_agent.ui.backend.service.AiAgentService._build_lead_chat_card", return_value={"type": "lead_paste"}):
                response = await AiAgentService.process_query(
                    db=mock_db,
                    user_query="manage lead 123",
                    conversation_id="conv-1"
                )
                
                assert response["intent"] == "MANAGE"
                assert response["record_id"] == "123"
                assert "chat_card" in response
                assert response["chat_card"]["type"] == "lead_paste"

@pytest.mark.asyncio
async def test_create_lead_returns_chat_card(mock_db):
    mock_lead = Lead(id="123", first_name="New", last_name="Lead", status="New")
    
    with patch("ai_agent.ui.backend.service.IntentPreClassifier.detect", return_value=None):
        with patch("ai_agent.ui.backend.service.AiAgentService._call_multi_llm_ensemble", return_value={"intent": "CREATE", "object_type": "lead", "data": {"last_name": "Lead", "status": "New"}}):
            with patch("ai_agent.ui.backend.service.LeadService.create_lead", return_value=mock_lead):
                with patch("ai_agent.ui.backend.service.AiAgentService._build_lead_chat_card", return_value={"type": "lead_paste"}):
                    response = await AiAgentService.process_query(
                        db=mock_db,
                        user_query="create lead",
                        conversation_id="conv-1"
                    )
                    
                    assert response["intent"] == "CREATE"
                    assert "chat_card" in response
                    assert response["chat_card"]["type"] == "lead_paste"
