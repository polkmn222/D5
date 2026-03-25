"""
Unit tests for Phase 171: AI Agent Lead CRUD Fix & Natural Transition
Tests verify:
1. Lead CREATE response overrides intent to OPEN_RECORD and includes redirect_url.
2. Lead UPDATE response overrides intent to OPEN_RECORD and includes redirect_url.
3. Lead DELETE properly calls the underlying deletion service.
"""

import pytest
from unittest.mock import MagicMock, patch
from ai_agent.ui.backend.service import AiAgentService

class MockLead:
    def __init__(self, record_id="TEST_LEAD_171", first_name="John", last_name="Doe", status="New",
                 email=None, phone=None, gender=None, brand=None, model=None, product=None,
                 description=None):
        self.id = record_id
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.email = email
        self.phone = phone
        self.gender = gender
        self.brand = brand
        self.model = model
        self.product = product
        self.description = description

class TestLeadCrudPhase171:
    def _run(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_lead_create_triggers_open_record(self):
        """Lead creation should return OPEN_RECORD intent with redirect_url."""
        mock_lead = MockLead(record_id="NEW171")
        db = MagicMock()

        agent_output = {
            "intent": "CREATE",
            "object_type": "lead",
            "data": {"first_name": "John", "last_name": "Doe", "status": "New"},
            "language_preference": "eng",
            "score": 1.0,
        }

        with patch("web.backend.app.services.lead_service.LeadService.create_lead", return_value=mock_lead), \
             patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=None), \
             patch("web.backend.app.services.model_service.ModelService.get_model", return_value=None), \
             patch("web.backend.app.services.product_service.ProductService.get_product", return_value=None), \
             patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.clear_pending_create"), \
             patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_created"), \
             patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_object"):
            
            result = self._run(AiAgentService._execute_intent(db, agent_output, "create lead John Doe"))

        assert result.get("intent") == "OPEN_RECORD"
        assert result.get("record_id") == "NEW171"
        assert result.get("redirect_url") == "/leads/NEW171"
        assert "has been created" in result.get("text", "")

    def test_lead_update_triggers_open_record(self):
        """Lead update should return OPEN_RECORD intent with redirect_url."""
        mock_lead = MockLead(record_id="UPD171", status="Qualified")
        db = MagicMock()

        agent_output = {
            "intent": "UPDATE",
            "object_type": "lead",
            "record_id": "UPD171",
            "data": {"status": "Qualified"},
            "language_preference": "eng",
            "score": 1.0,
        }

        with patch("web.backend.app.services.lead_service.LeadService.update_lead", return_value=mock_lead), \
             patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=mock_lead), \
             patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=None), \
             patch("web.backend.app.services.model_service.ModelService.get_model", return_value=None), \
             patch("web.backend.app.services.product_service.ProductService.get_product", return_value=None), \
             patch("ai_agent.llm.backend.conversation_context.ConversationContextStore.remember_object"):
            
            result = self._run(AiAgentService._execute_intent(db, agent_output, "update lead UPD171"))

        assert result.get("intent") == "OPEN_RECORD"
        assert result.get("redirect_url") == "/leads/UPD171"
        assert "has been updated" in result.get("text", "")

    def test_lead_delete_calls_service(self):
        """Lead deletion should call LeadService.delete_lead."""
        db = MagicMock()
        agent_output = {
            "intent": "DELETE",
            "object_type": "lead",
            "selection": {"ids": ["DEL171"], "object_type": "lead"}
        }

        with patch("web.backend.app.services.lead_service.LeadService.delete_lead", return_value=True) as mock_delete, \
             patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=MockLead(record_id="DEL171")):
             
            result = self._run(AiAgentService._execute_intent(db, agent_output, "delete lead DEL171"))
            
        mock_delete.assert_called_once_with(db, "DEL171")
        assert "deleted lead john doe" in result.get("text", "").lower()
