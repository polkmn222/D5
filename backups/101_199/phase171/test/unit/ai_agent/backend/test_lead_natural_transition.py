"""
Unit tests for Phase 169: AI Agent Lead Natural Transition
Tests verify:
1. Lead CREATE response contains natural transition message and chat_card
2. Lead UPDATE response contains natural transition message and chat_card
3. Chat card has Send Message action in its actions list
4. Bilingual response (Korean) is returned when language_preference is 'kor'
5. conversation context is remembered after create (for follow-up commands)
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Any


class MockLead:
    """Minimal mock lead object for testing."""
    def __init__(self, record_id="TEST_LEAD_169", first_name="길동", last_name="홍", status="New",
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


class TestLeadChatCardActions:
    """Tests for _build_lead_chat_card action structure."""

    def _get_service(self):
        # Import inline to avoid runtime DB errors at module level
        from ai_agent.backend.service import AiAgentService
        return AiAgentService

    def _make_mock_db(self):
        db = MagicMock()
        db.execute.return_value = MagicMock()
        return db

    def test_lead_chat_card_has_send_message_action(self):
        """Lead chat card in view mode should include a Send Message action."""
        from ai_agent.backend.service import AiAgentService

        db = self._make_mock_db()
        with patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=None), \
             patch("web.backend.app.services.model_service.ModelService.get_model", return_value=None), \
             patch("web.backend.app.services.product_service.ProductService.get_product", return_value=None):
            lead = MockLead()
            card = AiAgentService._build_lead_chat_card(db, lead, mode="view")

        assert card["type"] == "lead_paste"
        action_labels = [a["label"] for a in card.get("actions", [])]
        assert "Send Message" in action_labels, f"Expected 'Send Message' in actions, got: {action_labels}"

    def test_lead_chat_card_send_message_action_is_secondary(self):
        """Send Message action should have secondary tone."""
        from ai_agent.backend.service import AiAgentService

        db = self._make_mock_db()
        with patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=None), \
             patch("web.backend.app.services.model_service.ModelService.get_model", return_value=None), \
             patch("web.backend.app.services.product_service.ProductService.get_product", return_value=None):
            lead = MockLead()
            card = AiAgentService._build_lead_chat_card(db, lead, mode="view")

        actions_by_label = {a["label"]: a for a in card.get("actions", [])}
        send_msg = actions_by_label.get("Send Message")
        assert send_msg is not None
        assert send_msg.get("action") == "send_message"
        assert send_msg.get("tone") == "secondary"

    def test_lead_chat_card_no_send_message_in_edit_mode(self):
        """Lead chat card in edit mode should not have Send Message action."""
        from ai_agent.backend.service import AiAgentService

        db = self._make_mock_db()
        with patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=None), \
             patch("web.backend.app.services.model_service.ModelService.get_model", return_value=None), \
             patch("web.backend.app.services.product_service.ProductService.get_product", return_value=None):
            lead = MockLead()
            card = AiAgentService._build_lead_chat_card(db, lead, mode="edit")

        action_labels = [a["label"] for a in card.get("actions", [])]
        assert "Send Message" not in action_labels


class TestLeadCreateNaturalTransition:
    """Tests for natural transition message in lead CREATE intent."""

    def _run(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_lead_create_english_natural_message(self):
        """After lead creation with English preference, message should say 'has been created'."""
        from ai_agent.backend.service import AiAgentService

        mock_lead = MockLead(record_id="NEW169", first_name="John", last_name="Doe")
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
             patch("ai_agent.backend.conversation_context.ConversationContextStore.clear_pending_create"), \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.remember_created"), \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.remember_object"):
            result = self._run(AiAgentService._execute_intent(db, agent_output, "create lead John Doe status New"))

        assert result.get("intent") == "OPEN_RECORD"
        assert "has been created" in result.get("text", "").lower() or "created" in result.get("text", "").lower()
        assert "chat_card" in result
        assert result["chat_card"]["mode"] == "view"

    def test_lead_create_korean_natural_message(self):
        """After lead creation with Korean preference, message should contain Korean text."""
        from ai_agent.backend.service import AiAgentService

        mock_lead = MockLead(record_id="NEW169KR", first_name="길동", last_name="홍")
        db = MagicMock()

        agent_output = {
            "intent": "CREATE",
            "object_type": "lead",
            "data": {"first_name": "길동", "last_name": "홍", "status": "New"},
            "language_preference": "kor",
            "score": 1.0,
        }

        with patch("web.backend.app.services.lead_service.LeadService.create_lead", return_value=mock_lead), \
             patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=None), \
             patch("web.backend.app.services.model_service.ModelService.get_model", return_value=None), \
             patch("web.backend.app.services.product_service.ProductService.get_product", return_value=None), \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.clear_pending_create"), \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.remember_created"), \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.remember_object"):
            result = self._run(AiAgentService._execute_intent(db, agent_output, "리드 생성 홍 길동 상태 신규"))

        assert result.get("intent") == "OPEN_RECORD"
        # Check Korean text is present (contains Korean characters)
        text = result.get("text", "")
        assert any('\uAC00' <= c <= '\uD7A3' for c in text), f"Expected Korean text, got: {text}"
        assert "chat_card" in result

    def test_lead_create_sets_conversation_context(self):
        """After lead creation, conversation context should be remembered for follow-up commands."""
        from ai_agent.backend.service import AiAgentService

        mock_lead = MockLead(record_id="CTX169", first_name="Test", last_name="Context")
        db = MagicMock()

        agent_output = {
            "intent": "CREATE",
            "object_type": "lead",
            "data": {"first_name": "Test", "last_name": "Context", "status": "New"},
            "language_preference": "eng",
            "score": 1.0,
        }

        with patch("web.backend.app.services.lead_service.LeadService.create_lead", return_value=mock_lead), \
             patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=None), \
             patch("web.backend.app.services.model_service.ModelService.get_model", return_value=None), \
             patch("web.backend.app.services.product_service.ProductService.get_product", return_value=None), \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.clear_pending_create") as mock_clear, \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.remember_created") as mock_created, \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.remember_object") as mock_obj:
            result = self._run(AiAgentService._execute_intent(db, agent_output, "create lead", conversation_id="sess_169"))

        mock_created.assert_called_once()
        mock_obj.assert_called_once()
        # Verify remember_object is called with the created lead's id
        call_args = mock_obj.call_args
        assert str(mock_lead.id) in str(call_args)


class TestLeadUpdateNaturalTransition:
    """Tests for natural transition message in lead UPDATE intent."""

    def _run(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_lead_update_english_natural_message(self):
        """After lead update with English preference, message should say 'has been updated'."""
        from ai_agent.backend.service import AiAgentService

        mock_lead = MockLead(record_id="UPD169", first_name="John", last_name="Smith", status="Qualified")
        db = MagicMock()

        agent_output = {
            "intent": "UPDATE",
            "object_type": "lead",
            "record_id": "UPD169",
            "data": {"status": "Qualified"},
            "language_preference": "eng",
            "score": 1.0,
        }

        with patch("web.backend.app.services.lead_service.LeadService.update_lead", return_value=mock_lead), \
             patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=mock_lead), \
             patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=None), \
             patch("web.backend.app.services.model_service.ModelService.get_model", return_value=None), \
             patch("web.backend.app.services.product_service.ProductService.get_product", return_value=None), \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.remember_object"):
            result = self._run(AiAgentService._execute_intent(db, agent_output, "update lead UPD169 status Qualified"))

        text = result.get("text", "")
        assert "updated" in text.lower(), f"Expected 'updated' in response, got: {text}"
        assert "chat_card" in result
        assert result["chat_card"]["mode"] == "view"

    def test_lead_update_korean_natural_message(self):
        """After lead update with Korean preference, message should contain Korean text."""
        from ai_agent.backend.service import AiAgentService

        mock_lead = MockLead(record_id="UPD169KR", first_name="영희", last_name="김", status="Qualified")
        db = MagicMock()

        agent_output = {
            "intent": "UPDATE",
            "object_type": "lead",
            "record_id": "UPD169KR",
            "data": {"status": "Qualified"},
            "language_preference": "kor",
            "score": 1.0,
        }

        with patch("web.backend.app.services.lead_service.LeadService.update_lead", return_value=mock_lead), \
             patch("web.backend.app.services.lead_service.LeadService.get_lead", return_value=mock_lead), \
             patch("web.backend.app.services.vehicle_spec_service.VehicleSpecService.get_vehicle_spec", return_value=None), \
             patch("web.backend.app.services.model_service.ModelService.get_model", return_value=None), \
             patch("web.backend.app.services.product_service.ProductService.get_product", return_value=None), \
             patch("ai_agent.backend.conversation_context.ConversationContextStore.remember_object"):
            result = self._run(AiAgentService._execute_intent(db, agent_output, "리드 UPD169KR 상태 자격"))

        text = result.get("text", "")
        assert any('\uAC00' <= c <= '\uD7A3' for c in text), f"Expected Korean text, got: {text}"
        assert "chat_card" in result
