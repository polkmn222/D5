import pytest
from unittest.mock import patch, MagicMock
from db.models import Lead, Contact, Opportunity
from ai_agent.backend.service import AiAgentService

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.mark.asyncio
async def test_build_chat_card_supports_multiple_objects(mock_db):
    # Test Lead
    mock_lead = Lead(id="L1", first_name="John", last_name="Doe", status="New")
    card_lead = AiAgentService._build_chat_card(mock_db, "lead", mock_lead)
    assert card_lead["title"] == "John Doe"
    assert "Lead · New" in card_lead["subtitle"]
    
    # Test Contact
    mock_contact = Contact(id="C1", first_name="Jane", last_name="Smith", tier="A")
    card_contact = AiAgentService._build_chat_card(mock_db, "contact", mock_contact)
    assert card_contact["title"] == "Jane Smith"
    assert "Contact · A" in card_contact["subtitle"]
    
    # Test Opportunity
    mock_opp = Opportunity(id="O1", name="Big Deal", stage="Negotiation", amount=1000000)
    card_opp = AiAgentService._build_chat_card(mock_db, "opportunity", mock_opp)
    assert card_opp["title"] == "Big Deal"
    assert "Opportunity · Negotiation" in card_opp["subtitle"]
    assert any(f["label"] == "Amount" and "₩1,000,000" in f["value"] for f in card_opp["fields"])

@pytest.mark.asyncio
async def test_create_contact_returns_chat_card(mock_db):
    mock_contact = Contact(id="C1", first_name="Jane", last_name="Smith", tier="A")
    
    with patch("ai_agent.backend.service.IntentPreClassifier.detect", return_value=None):
        with patch("ai_agent.backend.service.AiAgentService._call_multi_llm_ensemble", return_value={"intent": "CREATE", "object_type": "contact", "data": {"last_name": "Smith"}}):
            with patch("web.backend.app.services.contact_service.ContactService.create_contact", return_value=mock_contact):
                # _build_chat_card is now called for contact too
                response = await AiAgentService.process_query(
                    db=mock_db,
                    user_query="create contact Smith",
                    conversation_id="conv-1"
                )
                
                assert response["intent"] == "CREATE"
                assert "chat_card" in response
                assert response["chat_card"]["object_type"] == "contact"
                assert response["chat_card"]["title"] == "Jane Smith"

@pytest.mark.asyncio
async def test_update_opportunity_returns_chat_card(mock_db):
    mock_opp = Opportunity(id="O1", name="Big Deal", stage="Closed Won", amount=1000000)
    
    with patch("ai_agent.backend.service.IntentPreClassifier.detect", return_value=None):
        with patch("ai_agent.backend.service.AiAgentService._call_multi_llm_ensemble", return_value={"intent": "UPDATE", "object_type": "opportunity", "record_id": "O1", "data": {"stage": "Closed Won"}}):
            with patch("web.backend.app.services.opportunity_service.OpportunityService.update_opportunity", return_value=True):
                with patch("web.backend.app.services.opportunity_service.OpportunityService.get_opportunity", return_value=mock_opp):
                    response = await AiAgentService.process_query(
                        db=mock_db,
                        user_query="update opportunity O1 to Closed Won",
                        conversation_id="conv-1"
                    )
                    
                    assert response["intent"] == "UPDATE"
                    assert "chat_card" in response
                    assert response["chat_card"]["object_type"] == "opportunity"
                    assert response["chat_card"]["mode"] == "edit"

@pytest.mark.asyncio
async def test_delete_confirmation_localized(mock_db):
    # Test Korean
    with patch("ai_agent.backend.service.ConversationContextStore.get_pending_delete", return_value=None):
        with patch("ai_agent.backend.service.ConversationContextStore.get_selection", return_value={"object_type": "lead", "ids": ["L1"], "labels": ["John Doe"]}):
            response_kor = await AiAgentService.process_query(
                db=mock_db,
                user_query="삭제해줘",
                conversation_id="conv-1",
                language_preference="kor"
            )
            assert "삭제 확인이 필요합니다" in response_kor["text"]
            assert "[예]" in response_kor["text"]

    # Test English
    with patch("ai_agent.backend.service.ConversationContextStore.get_pending_delete", return_value=None):
        with patch("ai_agent.backend.service.ConversationContextStore.get_selection", return_value={"object_type": "lead", "ids": ["L1"], "labels": ["John Doe"]}):
            response_eng = await AiAgentService.process_query(
                db=mock_db,
                user_query="delete it",
                conversation_id="conv-2",
                language_preference="eng"
            )
            assert "Delete confirmation needed" in response_eng["text"]
            assert "[yes]" in response_eng["text"]
