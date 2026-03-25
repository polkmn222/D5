"""
Unit tests for Phase 177: AI Agent Lead CRUD Enhancement
Tests specifically for:
1. Double confirmation bypass in DELETE flow.
2. Robustness of CREATE response handling service failures.
3. Expanded field extraction (brand, model, product).
"""

import pytest
from unittest.mock import MagicMock, patch
from ai_agent.ui.backend.service import AiAgentService

class MockLead:
    def __init__(self, record_id="TEST_LEAD_177", first_name="John", last_name="Doe", status="New"):
        self.id = record_id
        self.first_name = first_name
        self.last_name = last_name
        self.status = status

class TestLeadCrudPhase177:
    def _run(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_delete_trigger_bypass_double_confirmation(self):
        """
        Verify that explicit 'Delete lead {id}' bypasses confirmation.
        """
        db = MagicMock()
        conversation_id = "conv_177_delete"
        user_query = "Delete lead LEAD123"
        
        mock_lead = MockLead(record_id="LEAD123", first_name="John", last_name="Doe")
        with patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.get_context", return_value={"last_object": "lead", "last_record_id": "LEAD123"}), \
             patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_pending_delete") as mock_remember, \
             patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=mock_lead), \
             patch("web.backend.app.services.lead_service.LeadService.delete_lead", return_value=True):
            
            result = self._run(AiAgentService.process_query(db, user_query, conversation_id=conversation_id))
            
        # It should now return intent: DELETE directly
        assert result.get("intent") == "DELETE"
        assert "Deleted lead John Doe" in result.get("text", "")

    def test_create_lead_failure_handling(self):
        """
        Verify that if LeadService.create_lead returns None, 
        AiAgentService handles it gracefully.
        """
        db = MagicMock()
        agent_output = {
            "intent": "CREATE",
            "object_type": "lead",
            "data": {"last_name": "Error"},
            "language_preference": "eng"
        }
        
        with patch("web.backend.app.services.lead_service.LeadService.create_lead", return_value=None):
            result = self._run(AiAgentService._execute_intent(db, agent_output, "create lead Error"))
            assert result.get("intent") == "CHAT"
            assert "error" in result.get("text", "").lower()

    def test_field_extraction_includes_new_fields(self):
        """
        Verify that brand, model, and product are extracted from text.
        """
        query = "change brand to Kia, model to K5, and product to K5-GT"
        data = AiAgentService._extract_lead_update_fields_from_text(query)
        
        assert data.get("brand") == "Kia"
        assert data.get("model") == "K5"
        assert data.get("product") == "K5-GT"

    def test_direct_edit_intent_opens_form(self):
        """
        Verify that 'Edit lead LEAD123' directly returns OPEN_FORM intent.
        """
        db = MagicMock()
        conversation_id = "conv_177_edit"
        user_query = "edit lead LEAD123"
        
        mock_lead = MockLead(record_id="LEAD123", first_name="John", last_name="Doe")
        
        with patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.get_context", return_value={"last_object": "lead", "last_record_id": "LEAD123", "last_intent": "MANAGE"}), \
             patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=mock_lead):
            
            result = self._run(AiAgentService.process_query(db, user_query, conversation_id=conversation_id))
            
        assert result.get("intent") == "OPEN_FORM"
        assert result.get("form_url") == "/leads/new-modal?id=LEAD123"
