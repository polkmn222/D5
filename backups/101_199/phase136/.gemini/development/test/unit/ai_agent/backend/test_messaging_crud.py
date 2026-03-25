import pytest
import uuid
from unittest.mock import patch, AsyncMock
from db.database import Base, engine, SessionLocal
from ai_agent.backend.service import AiAgentService
from ai_agent.backend.intent_preclassifier import IntentPreClassifier
from db.models import MessageTemplate, MessageSend, Contact

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.mark.asyncio
async def test_ai_message_template_crud_flow(db):
    unique_id = uuid.uuid4().hex[:8]
    test_template_name = f"Welcome SMS-{unique_id}"

    mock_create_template = {
        "intent": "CREATE",
        "object_type": "message_template",
        "data": {"name": test_template_name, "subject": "Welcome", "content": "Hello, welcome!"},
        "text": "Creating template.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_create_template
        res = await AiAgentService.process_query(db, f"Create template {test_template_name} with content Hello, welcome!")
        assert "Success! Created Template" in res["text"]
        template = db.query(MessageTemplate).filter(MessageTemplate.name == test_template_name).first()
        assert template is not None
        template_id = template.id

    mock_query_template = {
        "intent": "QUERY",
        "object_type": "message_template",
        "sql": f"SELECT id, name, subject FROM message_templates WHERE id = '{template_id}'",
        "text": "Found the template.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_template
        res = await AiAgentService.process_query(db, f"Show me template {template_id}")
        assert len(res["results"]) > 0
        assert res["results"][0]["name"] == test_template_name

    mock_update_template = {
        "intent": "UPDATE",
        "object_type": "message_template",
        "record_id": template_id,
        "data": {"content": "Updated welcome message."},
        "text": "Updating template content.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_update_template
        res = await AiAgentService.process_query(db, f"Update template {template_id} content to Updated welcome message.")
        assert "Success! Updated Template" in res["text"]
        db.refresh(template)
        assert template.content == "Updated welcome message."

    mock_delete_template = {
        "intent": "DELETE",
        "object_type": "message_template",
        "record_id": template_id,
        "text": "Deleting template.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_delete_template
        res = await AiAgentService.process_query(db, f"Delete template {template_id}")
        assert "Success! Deleted Message Template" in res["text"]
        deleted_template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        assert deleted_template is not None
        assert deleted_template.deleted_at is not None

@pytest.mark.asyncio
async def test_ai_message_send_query(db):
    unique_id = uuid.uuid4().hex[:8]
    contact_id = f"CNT-{unique_id}"
    template_id = f"MT-{unique_id}"
    msg_send_id = f"MS-{unique_id}"

    contact = Contact(id=contact_id, first_name="Jane", last_name="Doe", email=f"jane-{unique_id}@example.com")
    template = MessageTemplate(id=template_id, name=f"Test Temp-{unique_id}", subject="Hi", content="Test content")
    db.add_all([contact, template])
    db.commit()

    msg_send = MessageSend(
        id=msg_send_id,
        contact=contact.id,
        template=template.id,
        content="Test message",
        direction="Outbound",
        status="Sent",
    )
    db.add(msg_send)
    db.commit()

    mock_query_message = {
        "intent": "QUERY",
        "object_type": "message_send",
        "sql": f"SELECT id, contact, template, status, sent_at FROM message_sends WHERE id = '{msg_send.id}'",
        "text": "Found the message.",
        "score": 1.0,
    }
    with patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_message
        res = await AiAgentService.process_query(db, f"Show me message {msg_send.id}")
        assert len(res["results"]) > 0
        assert res["results"][0]["status"] == "Sent"

    mock_query_messages_by_contact = {
        "intent": "QUERY",
        "object_type": "message_send",
        "sql": f"SELECT id, contact, template, status, sent_at FROM message_sends WHERE contact = '{contact.id}'",
        "text": "Found messages for contact.",
        "score": 1.0,
    }
    with patch.object(IntentPreClassifier, "detect", return_value=None), \
         patch.object(AiAgentService, "_call_multi_llm_ensemble", new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query_messages_by_contact
        res = await AiAgentService.process_query(db, f"Show me messages for contact {contact.id}")
        assert len(res["results"]) > 0
        first_row = res["results"][0]
        assert first_row.get("contact") == contact.id
