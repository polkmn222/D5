import importlib

import pytest
from fastapi.testclient import TestClient

from ai_agent.backend.conversation_context import ConversationContextStore
from ai_agent.backend.main import app as ai_agent_app
from ai_agent.backend.service import AiAgentService


DELETE_CASES = [
    ("lead", "delete that lead", "web.backend.app.services.lead_service", "LeadService", "delete_lead"),
    ("contact", "delete that contact", "web.backend.app.services.contact_service", "ContactService", "delete_contact"),
    ("opportunity", "delete that opportunity", "web.backend.app.services.opportunity_service", "OpportunityService", "delete_opportunity"),
    ("brand", "delete that brand", "web.backend.app.services.vehicle_spec_service", "VehicleSpecService", "delete_vehicle_spec"),
    ("model", "delete that model", "web.backend.app.services.model_service", "ModelService", "delete_model"),
    ("product", "delete that product", "web.backend.app.services.product_service", "ProductService", "delete_product"),
    ("asset", "delete that asset", "web.backend.app.services.asset_service", "AssetService", "delete_asset"),
    ("message_template", "delete that template", "web.message.backend.services.message_template_service", "MessageTemplateService", "delete_template"),
]


@pytest.fixture
def client():
    return TestClient(ai_agent_app)


@pytest.mark.parametrize("object_type, query, _module_path, _class_name, _method_name", DELETE_CASES)
def test_delete_request_requires_confirmation_for_all_objects(
    client,
    monkeypatch,
    object_type,
    query,
    _module_path,
    _class_name,
    _method_name,
):
    conversation_id = f"conv-delete-confirm-{object_type}"
    ConversationContextStore.clear(conversation_id)
    ConversationContextStore.remember_object(conversation_id, object_type, "MANAGE", record_id=f"{object_type}-001")

    async def fail_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called for delete confirmation")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)

    response = client.post("/api/chat", json={"query": query, "conversation_id": conversation_id})
    data = response.json()

    assert data["intent"] == "CHAT"
    assert "Delete confirmation needed" in data["text"]
    assert "Reply 'yes'" in data["text"]
    pending = ConversationContextStore.get_pending_delete(conversation_id)
    assert pending["object_type"] == object_type
    assert pending["record_id"] == f"{object_type}-001"


@pytest.mark.parametrize("object_type, query, module_path, class_name, method_name", DELETE_CASES)
def test_delete_confirmation_executes_for_all_objects(
    client,
    monkeypatch,
    object_type,
    query,
    module_path,
    class_name,
    method_name,
):
    conversation_id = f"conv-delete-run-{object_type}"
    ConversationContextStore.clear(conversation_id)
    ConversationContextStore.remember_object(conversation_id, object_type, "MANAGE", record_id=f"{object_type}-002")

    async def fail_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called for delete confirmation or execution")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)

    first = client.post("/api/chat", json={"query": query, "conversation_id": conversation_id})
    assert first.json()["intent"] == "CHAT"

    calls = []

    module = importlib.import_module(module_path)
    service_class = getattr(module, class_name)

    def fake_delete(db, record_id):
        calls.append(record_id)
        return True

    monkeypatch.setattr(service_class, method_name, fake_delete)

    confirm = client.post("/api/chat", json={"query": "yes", "conversation_id": conversation_id})
    data = confirm.json()

    assert calls == [f"{object_type}-002"]
    assert data["intent"] == "DELETE"
    assert "Success! Deleted" in data["text"]
    assert ConversationContextStore.get_pending_delete(conversation_id) == {}


def test_delete_confirmation_can_be_cancelled(client, monkeypatch):
    conversation_id = "conv-delete-cancel"
    ConversationContextStore.clear(conversation_id)
    ConversationContextStore.remember_object(conversation_id, "lead", "MANAGE", record_id="lead-003")

    async def fail_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called for delete cancel flow")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)

    client.post("/api/chat", json={"query": "delete that lead", "conversation_id": conversation_id})
    response = client.post("/api/chat", json={"query": "cancel", "conversation_id": conversation_id})
    data = response.json()

    assert data["intent"] == "CHAT"
    assert data["text"] == "Delete request cancelled."
    assert ConversationContextStore.get_pending_delete(conversation_id) == {}
