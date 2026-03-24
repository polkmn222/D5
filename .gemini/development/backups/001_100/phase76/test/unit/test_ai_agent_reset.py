from fastapi.testclient import TestClient

from ai_agent.backend.conversation_context import ConversationContextStore
from ai_agent.backend.main import app as ai_agent_app


def test_reset_endpoint_clears_conversation_context():
    client = TestClient(ai_agent_app)
    conversation_id = "conv-reset-1"

    ConversationContextStore.remember_created(conversation_id, "lead", "lead-999")
    assert ConversationContextStore.get_context(conversation_id)["last_created"]["record_id"] == "lead-999"

    response = client.post("/api/reset", json={"conversation_id": conversation_id})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert ConversationContextStore.get_context(conversation_id) == {}
