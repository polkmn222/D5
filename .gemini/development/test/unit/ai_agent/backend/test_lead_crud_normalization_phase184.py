import pytest
from unittest.mock import MagicMock, patch
import asyncio

from ai_agent.ui.backend.service import AiAgentService

class MockLead:
    def __init__(self, id="LEAD_123", first_name="John", last_name="Doe", status="New"):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.brand = None
        self.model = None
        self.product = None
        self.description = None
        self.email = "test@example.com"
        self.phone = "010-1234-5678"
        self.gender = "Male"

class MockContact:
    def __init__(self, id="CONT_456", first_name="Jane", last_name="Doe"):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.name = f"{first_name} {last_name}"

class MockOpportunity:
    def __init__(self, id="OPP_789", name="Test Deal"):
        self.id = id
        self.name = name

@pytest.mark.asyncio
async def test_lead_create_returns_open_record_and_chat_card():
    mock_lead = MockLead()
    db = MagicMock()
    
    agent_output = {
        "intent": "CREATE",
        "object_type": "lead",
        "data": {"first_name": "John", "last_name": "Doe", "status": "New"},
        "language_preference": "eng",
        "score": 1.0,
    }
    
    with patch("web.backend.app.services.lead_service.LeadService.create_lead", return_value=mock_lead), \
         patch("ai_agent.ui.backend.service.AiAgentService._build_lead_chat_card", return_value={"type": "lead_paste", "actions": [{"label": "Open Record"}]}), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.clear_pending_create"), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_created"), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_object"):
        
        result = await AiAgentService._execute_intent(db, agent_output, "create lead John Doe")
        
        assert result["intent"] == "OPEN_RECORD"
        assert result["redirect_url"] == f"/leads/{mock_lead.id}"
        assert "chat_card" in result
        assert result["chat_card"]["actions"][0]["label"] == "Open Record"

@pytest.mark.asyncio
async def test_lead_update_returns_open_record_and_chat_card():
    mock_lead = MockLead()
    db = MagicMock()
    
    agent_output = {
        "intent": "UPDATE",
        "object_type": "lead",
        "record_id": "LEAD_123",
        "data": {"status": "Qualified"},
        "language_preference": "eng",
        "score": 1.0,
    }
    
    with patch("web.backend.app.services.lead_service.LeadService.update_lead", return_value=mock_lead), \
         patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=mock_lead), \
         patch("ai_agent.ui.backend.service.AiAgentService._build_lead_chat_card", return_value={"type": "lead_paste", "actions": [{"label": "Open Record"}]}), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_object"):
        
        result = await AiAgentService._execute_intent(db, agent_output, "update lead LEAD_123 status Qualified")
        
        assert result["intent"] == "OPEN_RECORD"
        assert result["redirect_url"] == "/leads/LEAD_123"
        assert "chat_card" in result
        assert result["chat_card"]["actions"][0]["label"] == "Open Record"

@pytest.mark.asyncio
async def test_delete_with_force_flag_bypasses_confirmation():
    db = MagicMock()
    conversation_id = "test_conv"
    
    # Mock context to have a last record
    with patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.get_context", return_value={"last_object": "lead", "last_record_id": "LEAD_123"}), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.get_pending_delete", return_value=None), \
         patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.get_selection", return_value=None):
        
        # This should return intent: DELETE directly
        result = AiAgentService._resolve_delete_confirmation("[FORCE_DELETE] Delete lead", conversation_id)
        
        assert result["intent"] == "DELETE"
        assert result["record_id"] == "LEAD_123"

def test_default_query_parts_consistency():
    parts = AiAgentService._default_query_parts("lead")
    assert "TRIM(CONCAT_WS" in parts["select"]
    assert "model_name" in parts["select"]
    assert "LEFT JOIN models" in parts["from"]

    parts = AiAgentService._default_query_parts("opportunity")
    assert "TRIM(CONCAT_WS" in parts["select"]
    assert "model_name" in parts["select"]
    assert "LEFT JOIN models" in parts["from"]
