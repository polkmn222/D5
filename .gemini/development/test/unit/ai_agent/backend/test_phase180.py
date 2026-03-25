
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT))

from ai_agent.ui.backend.service import AiAgentService

class TestPhase180:
    def test_display_value_empty(self):
        """Test that empty values return an empty string instead of 'Blank'."""
        assert AiAgentService._display_value(None) == ""
        assert AiAgentService._display_value("") == ""
        assert AiAgentService._display_value("None") == ""
        assert AiAgentService._display_value("null") == ""
        
        # Non-empty values should still work
        assert AiAgentService._display_value("Test") == "Test"
        assert AiAgentService._display_value(True) == "Yes"
        assert AiAgentService._display_value(False) == "No"

    def test_lead_delete_summary(self):
        """Test lead delete summary handles empty phone correctly."""
        mock_lead = MagicMock()
        mock_lead.first_name = "John"
        mock_lead.last_name = "Doe"
        
        # With phone
        mock_lead.phone = "010-1234-5678"
        summary = AiAgentService._lead_delete_summary(mock_lead)
        assert summary == "John Doe (010-1234-5678)"
        
        # Without phone
        mock_lead.phone = None
        summary = AiAgentService._lead_delete_summary(mock_lead)
        assert summary == "John Doe"

    def test_default_query_parts_lead(self):
        """Test that lead query parts align with AGENT_TABLE_SCHEMAS."""
        config = AiAgentService._default_query_parts("lead")
        assert config is not None
        # display_name, phone, status, model, created_at
        assert "TRIM(CONCAT_WS(' ', l.first_name, l.last_name)) AS display_name" in config["select"]
        assert "l.phone" in config["select"]
        assert "l.status" in config["select"]
        assert "COALESCE(m.name, l.model) AS model" in config["select"]
        assert "l.created_at" in config["select"]
        assert "leads l LEFT JOIN models m ON l.model = m.id" in config["from"]

    @pytest.mark.asyncio
    async def test_execute_intent_manage_no_id_exposure(self):
        """Test that MANAGE intent text does not expose ID."""
        db = MagicMock()
        agent_output = {
            "intent": "MANAGE",
            "object_type": "lead",
            "record_id": "lead-123"
        }
        user_query = "manage lead lead-123"
        
        # Mock LeadService.get_lead and other dependencies
        mock_lead = MagicMock()
        mock_lead.id = "lead-123"
        mock_lead.first_name = "John"
        mock_lead.last_name = "Doe"
        mock_lead.status = "New"
        mock_lead.phone = None
        mock_lead.email = None
        mock_lead.gender = None
        mock_lead.brand = None
        mock_lead.model = None
        mock_lead.product = None
        mock_lead.description = None

        with MagicMock() as mock_lead_service:
            # We need to patch the classes used inside _execute_intent
            import ai_agent.ui.backend.service as service_mod
            original_lead_service = service_mod.LeadService
            service_mod.LeadService = MagicMock()
            service_mod.LeadService.get_lead.return_value = mock_lead
            
            try:
                # Mock _build_lead_chat_card to return something
                AiAgentService._build_lead_chat_card = MagicMock(return_value={"type": "lead_paste"})
                
                res = await AiAgentService._execute_intent(db, agent_output, user_query)
                # For leads, it uses a different text format
                assert "Lead **John Doe** is now open" in res["text"]
                assert "(ID: lead-123)" not in res["text"]
                
                # Test for another object type to verify the generic message
                agent_output_contact = {
                    "intent": "MANAGE",
                    "object_type": "contact",
                    "record_id": "contact-456"
                }
                # Mock ContactService.get_contact
                service_mod.ContactService = MagicMock()
                mock_contact = MagicMock()
                mock_contact.first_name = "Alice"
                mock_contact.last_name = "Smith"
                mock_contact.email = "alice@test.com"
                service_mod.ContactService.get_contact.return_value = mock_contact
                
                res_contact = await AiAgentService._execute_intent(db, agent_output_contact, "manage contact contact-456")
                assert "I've selected **Contact: Alice Smith (alice@test.com)**" in res_contact["text"]
                assert "(ID: contact-456)" not in res_contact["text"]
                
            finally:
                service_mod.LeadService = original_lead_service

if __name__ == "__main__":
    pytest.main([__file__])
