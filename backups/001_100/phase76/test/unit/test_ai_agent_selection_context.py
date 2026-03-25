from fastapi.testclient import TestClient

from ai_agent.backend.conversation_context import ConversationContextStore
from ai_agent.backend.main import app as ai_agent_app
from ai_agent.backend.service import AiAgentService


def test_selection_payload_is_saved_in_conversation_context(monkeypatch):
    client = TestClient(ai_agent_app)
    conversation_id = "conv-selection-1"
    ConversationContextStore.clear(conversation_id)

    async def fake_llm(user_query: str, system_prompt: str):
        return {"intent": "CHAT", "text": "selection saved", "score": 0.2}

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_llm)

    selection = {"object_type": "lead", "ids": ["lead-1", "lead-2", "lead-3"]}
    response = client.post(
        "/api/chat",
        json={"query": "show all leads", "conversation_id": conversation_id, "selection": selection},
    )

    assert response.status_code == 200
    assert ConversationContextStore.get_selection(conversation_id) == selection


def test_reset_clears_selection_context(monkeypatch):
    client = TestClient(ai_agent_app)
    conversation_id = "conv-selection-2"
    ConversationContextStore.clear(conversation_id)
    ConversationContextStore.remember_selection(conversation_id, {"object_type": "contact", "ids": ["contact-1"]})

    async def fake_llm(user_query: str, system_prompt: str):
        return {"intent": "CHAT", "text": "ok", "score": 0.1}

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_llm)

    reset_res = client.post("/api/reset", json={"conversation_id": conversation_id})

    assert reset_res.status_code == 200
    assert ConversationContextStore.get_selection(conversation_id) == {}
