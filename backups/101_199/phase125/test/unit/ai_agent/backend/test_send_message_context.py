import pytest
from fastapi.testclient import TestClient

from ai_agent.backend.conversation_context import ConversationContextStore
from ai_agent.backend.main import app as ai_agent_app
from ai_agent.backend.service import AiAgentService


SELECTION_OBJECTS = [
    "lead",
    "contact",
    "opportunity",
    "brand",
    "model",
    "product",
    "asset",
    "message_template",
]


@pytest.fixture
def client():
    return TestClient(ai_agent_app)


@pytest.mark.parametrize("object_type", SELECTION_OBJECTS)
def test_send_message_uses_selection_context_for_all_objects(client, monkeypatch, object_type):
    conversation_id = f"conv-send-{object_type}"
    ConversationContextStore.clear(conversation_id)

    async def fail_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called for selection-based send message flow")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)

    selection = {"object_type": object_type, "ids": [f"{object_type}-1", f"{object_type}-2"]}
    response = client.post(
        "/api/chat",
        json={"query": "send message", "conversation_id": conversation_id, "selection": selection},
    )
    data = response.json()

    assert data["intent"] == "SEND_MESSAGE"
    assert data["selection"] == selection
    assert data["redirect_url"].startswith("/messaging/ui?")


def test_send_message_without_selection_asks_for_records(client, monkeypatch):
    conversation_id = "conv-send-empty"
    ConversationContextStore.clear(conversation_id)

    async def fail_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called when send message has no selection")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)

    response = client.post(
        "/api/chat",
        json={"query": "send message", "conversation_id": conversation_id},
    )
    data = response.json()

    assert data["intent"] == "CHAT"
    assert "Who should I send the message to?" in data["text"]


def test_send_message_carries_last_managed_template_id(client, monkeypatch):
    conversation_id = "conv-send-template"
    ConversationContextStore.clear(conversation_id)

    async def fail_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called for template-aware send message flow")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)
    ConversationContextStore.remember_object(conversation_id, "message_template", "MANAGE", record_id="tpl-101")

    selection = {"object_type": "contact", "ids": ["contact-1"]}
    response = client.post(
        "/api/chat",
        json={"query": "send message using this template", "conversation_id": conversation_id, "selection": selection},
    )
    data = response.json()

    assert data["intent"] == "SEND_MESSAGE"
    assert data["template_id"] == "tpl-101"


def test_send_message_with_template_phrase_requires_current_template(client, monkeypatch):
    conversation_id = "conv-send-template-missing"
    ConversationContextStore.clear(conversation_id)

    async def fail_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called for explicit template send guidance")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)

    selection = {"object_type": "contact", "ids": ["contact-1"]}
    response = client.post(
        "/api/chat",
        json={"query": "send message with this template", "conversation_id": conversation_id, "selection": selection},
    )
    data = response.json()

    assert data["intent"] == "CHAT"
    assert "need a current template first" in data["text"]
