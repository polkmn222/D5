from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from ai_agent.backend.conversation_context import ConversationContextStore
from ai_agent.backend.main import app as ai_agent_app
from ai_agent.backend.service import AiAgentService
from web.backend.app.services.lead_service import LeadService


@pytest.fixture
def client():
    return TestClient(ai_agent_app)


def test_conversation_memory_resolves_just_created_record(client, monkeypatch):
    conversation_id = "conv-memory-1"
    ConversationContextStore.clear(conversation_id)

    calls = {"count": 0}

    async def fake_ensemble(user_query: str, system_prompt: str):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "intent": "CREATE",
                "object_type": "lead",
                "data": {"last_name": "Kim", "status": "New"},
                "score": 0.95,
            }
        raise AssertionError("LLM should not be called for the follow-up recent-record request")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_ensemble)
    monkeypatch.setattr(
        LeadService,
        "create_lead",
        lambda db, **data: SimpleNamespace(id="lead-101", first_name="", last_name=data["last_name"], status=data["status"]),
    )
    monkeypatch.setattr(
        LeadService,
        "get_lead",
        lambda db, record_id: SimpleNamespace(id=record_id, first_name="", last_name="Kim", status="New"),
    )

    create_res = client.post(
        "/api/chat",
        json={
            "query": "create lead last name Kim status New",
            "conversation_id": conversation_id,
        },
    )
    create_data = create_res.json()

    assert create_data["text"].startswith("Success! Created lead")
    assert create_data["chat_card"]["type"] == "lead_paste"
    assert create_data["chat_card"]["mode"] == "view"
    assert [action["label"] for action in create_data["chat_card"]["actions"]] == ["Edit", "Delete"]

    follow_res = client.post(
        "/api/chat",
        json={
            "query": "show the lead I just created",
            "conversation_id": conversation_id,
        },
    )
    follow_data = follow_res.json()

    assert follow_data["intent"] == "MANAGE"
    assert follow_data["record_id"] == "lead-101"
    assert "Kim" in follow_data["text"]
    assert follow_data["chat_card"]["type"] == "lead_paste"
    assert follow_data["chat_card"]["mode"] == "view"


def test_recent_reference_does_not_leak_between_conversations(client, monkeypatch):
    source_conversation = "conv-memory-2-source"
    other_conversation = "conv-memory-2-other"
    ConversationContextStore.clear(source_conversation)
    ConversationContextStore.clear(other_conversation)

    async def fake_ensemble(user_query: str, system_prompt: str):
        return {"intent": "CHAT", "text": "fallback", "score": 0.2}

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_ensemble)
    ConversationContextStore.remember_created(source_conversation, "lead", "lead-202")

    res = client.post(
        "/api/chat",
        json={
            "query": "show the lead I just created",
            "conversation_id": other_conversation,
        },
    )
    data = res.json()

    assert data["intent"] == "QUERY"
    assert data["object_type"] == "lead"
    assert data.get("record_id") in (None, "")


def test_follow_up_update_reference_uses_last_record_context(client, monkeypatch):
    conversation_id = "conv-memory-3"
    ConversationContextStore.clear(conversation_id)

    calls = {"count": 0}

    async def fake_ensemble(user_query: str, system_prompt: str):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "intent": "CREATE",
                "object_type": "lead",
                "data": {"last_name": "Park", "status": "Working"},
                "score": 0.95,
            }
        raise AssertionError("LLM should not be called for contextual follow-up update request")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_ensemble)
    monkeypatch.setattr(
        LeadService,
        "create_lead",
        lambda db, **data: SimpleNamespace(id="lead-303", first_name="", last_name=data["last_name"], status=data["status"]),
    )
    monkeypatch.setattr(
        LeadService,
        "get_lead",
        lambda db, record_id: SimpleNamespace(id=record_id, first_name="", last_name="Park", status="Working"),
    )

    client.post(
        "/api/chat",
        json={
            "query": "create lead last name Park status Working",
            "conversation_id": conversation_id,
        },
    )

    follow_res = client.post(
        "/api/chat",
        json={
            "query": "그 리드 수정해줘",
            "conversation_id": conversation_id,
        },
    )
    follow_data = follow_res.json()

    assert follow_data["intent"] == "OPEN_FORM"
    assert follow_data["record_id"] == "lead-303"
    assert follow_data["form_url"] == "/leads/new-modal?id=lead-303"
    assert "edit form" in follow_data["text"]


def test_follow_up_pronoun_uses_last_managed_record(client, monkeypatch):
    conversation_id = "conv-memory-4"
    ConversationContextStore.clear(conversation_id)

    calls = {"count": 0}

    async def fake_llm(user_query: str, system_prompt: str):
        calls["count"] += 1
        if calls["count"] == 1:
            return {"intent": "CHAT", "text": "fallback", "score": 0.1}
        raise AssertionError("LLM should not be called for pronoun follow-up request")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_llm)
    monkeypatch.setattr(
        LeadService,
        "get_lead",
        lambda db, record_id: SimpleNamespace(id=record_id, first_name="", last_name="Lee", status="Qualified"),
    )

    manage_res = client.post(
        "/api/chat",
        json={
            "query": "Manage lead lead-404",
            "conversation_id": conversation_id,
        },
    )
    manage_data = manage_res.json()
    assert manage_data["record_id"] == "lead-404"
    assert [action["label"] for action in manage_data["chat_card"]["actions"]] == ["Edit", "Delete"]

    follow_res = client.post(
        "/api/chat",
        json={
            "query": "그거 수정해줘",
            "conversation_id": conversation_id,
        },
    )
    follow_data = follow_res.json()

    assert follow_data["intent"] == "OPEN_FORM"
    assert follow_data["record_id"] == "lead-404"
    assert follow_data["form_url"] == "/leads/new-modal?id=lead-404"


def test_lead_update_returns_refreshed_chat_card(client, monkeypatch):
    conversation_id = "conv-memory-5"
    ConversationContextStore.clear(conversation_id)

    async def fake_llm(user_query: str, system_prompt: str):
        return {
            "intent": "UPDATE",
            "object_type": "lead",
            "record_id": "lead-505",
            "data": {"status": "Qualified"},
            "score": 0.95,
        }

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_llm)
    monkeypatch.setattr(LeadService, "update_lead", lambda db, record_id, **data: True)
    monkeypatch.setattr(
        LeadService,
        "get_lead",
        lambda db, record_id: SimpleNamespace(
            id=record_id,
            first_name="Min",
            last_name="Cho",
            status="Qualified",
            email="min.cho@test.com",
            phone="01012345678",
            gender=None,
            brand=None,
            model=None,
            product=None,
            description="Ready for follow up",
        ),
    )

    res = client.post(
        "/api/chat",
        json={
            "query": "update lead 505 to qualified",
            "conversation_id": conversation_id,
        },
    )
    data = res.json()

    assert data["text"].startswith("Success! Updated Lead lead-505")
    assert data["chat_card"]["type"] == "lead_paste"
    assert data["chat_card"]["mode"] == "edit"


def test_field_only_follow_up_updates_current_editing_lead_without_llm(client, monkeypatch):
    conversation_id = "conv-memory-6"
    ConversationContextStore.clear(conversation_id)

    lead_state = {
        "id": "lead-606",
        "first_name": "Ji",
        "last_name": "Han",
        "status": "Working",
        "email": "ji.han@test.com",
        "phone": "01000000000",
        "gender": None,
        "brand": None,
        "model": None,
        "product": None,
        "description": "Initial note",
    }
    updated = {}

    async def fake_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called for field-only lead edit follow-up")

    def build_lead_state() -> SimpleNamespace:
        return SimpleNamespace(**lead_state)

    def fake_update(db, record_id, **data):
        assert record_id == "lead-606"
        updated.update(data)
        lead_state.update(data)
        return True

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_llm)
    monkeypatch.setattr(LeadService, "get_lead", lambda db, record_id: build_lead_state())
    monkeypatch.setattr(LeadService, "update_lead", fake_update)
    ConversationContextStore.remember_object(conversation_id, "lead", "MANAGE", record_id="lead-606")

    follow_res = client.post(
        "/api/chat",
        json={
            "query": "status Qualified",
            "conversation_id": conversation_id,
        },
    )
    follow_data = follow_res.json()

    assert updated == {"status": "Qualified"}
    assert follow_data["text"].startswith("Success! Updated Lead lead-606")
    assert follow_data["chat_card"]["type"] == "lead_paste"
    assert follow_data["chat_card"]["mode"] == "edit"
    assert follow_data["chat_card"]["fields"][2]["value"] == "Qualified"


def test_create_card_follow_up_field_update_uses_created_lead_context(client, monkeypatch):
    conversation_id = "conv-memory-7"
    ConversationContextStore.clear(conversation_id)

    calls = {"count": 0}
    lead_state = {
        "id": "lead-707",
        "first_name": "",
        "last_name": "Seo",
        "status": "New",
        "email": None,
        "phone": None,
        "gender": None,
        "brand": None,
        "model": None,
        "product": None,
        "description": None,
    }

    async def fake_llm(user_query: str, system_prompt: str):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "intent": "CREATE",
                "object_type": "lead",
                "data": {"last_name": "Seo", "status": "New"},
                "score": 0.95,
            }
        raise AssertionError("LLM should not be called for created-lead field follow-up")

    def build_lead_state() -> SimpleNamespace:
        return SimpleNamespace(**lead_state)

    def fake_update(db, record_id, **data):
        assert record_id == "lead-707"
        lead_state.update(data)
        return True

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_llm)
    monkeypatch.setattr(LeadService, "create_lead", lambda db, **data: build_lead_state())
    monkeypatch.setattr(LeadService, "get_lead", lambda db, record_id: build_lead_state())
    monkeypatch.setattr(LeadService, "update_lead", fake_update)

    create_res = client.post(
        "/api/chat",
        json={
            "query": "create lead last name Seo status New",
            "conversation_id": conversation_id,
        },
    )
    create_data = create_res.json()
    assert create_data["chat_card"]["mode"] == "view"

    follow_res = client.post(
        "/api/chat",
        json={
            "query": "phone 010-1234-5678",
            "conversation_id": conversation_id,
        },
    )
    follow_data = follow_res.json()

    assert calls["count"] == 1
    assert lead_state["phone"] == "01012345678"
    assert follow_data["chat_card"]["mode"] == "edit"
    assert follow_data["chat_card"]["fields"][4]["value"] == "01012345678"


def test_confirmed_lead_delete_uses_name_and_phone_in_success_copy(client, monkeypatch):
    conversation_id = "conv-memory-8"
    ConversationContextStore.clear(conversation_id)

    async def fake_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called for contextual lead delete confirmation")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_llm)
    monkeypatch.setattr(
        LeadService,
        "get_lead",
        lambda db, record_id: SimpleNamespace(id=record_id, first_name="Min", last_name="Cho", phone="01012345678"),
    )
    monkeypatch.setattr(LeadService, "delete_lead", lambda db, record_id: True)
    ConversationContextStore.remember_object(conversation_id, "lead", "MANAGE", record_id="lead-808")

    confirm_res = client.post(
        "/api/chat",
        json={
            "query": "Delete lead lead-808",
            "conversation_id": conversation_id,
        },
    )
    confirm_data = confirm_res.json()
    assert "Delete confirmation needed" in confirm_data["text"]

    delete_res = client.post(
        "/api/chat",
        json={
            "query": "yes",
            "conversation_id": conversation_id,
        },
    )
    delete_data = delete_res.json()

    assert delete_data["text"] == "Success! Deleted lead Min Cho (01012345678)."


def test_recent_korean_created_lead_request_uses_conversation_memory(client, monkeypatch):
    conversation_id = "conv-memory-9"
    ConversationContextStore.clear(conversation_id)

    calls = {"count": 0}

    async def fake_ensemble(user_query: str, system_prompt: str):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "intent": "CREATE",
                "object_type": "lead",
                "data": {"last_name": "Kim", "status": "New"},
                "score": 0.95,
            }
        raise AssertionError("LLM should not be called for recent created lead recall")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_ensemble)
    monkeypatch.setattr(
        LeadService,
        "create_lead",
        lambda db, **data: SimpleNamespace(id="lead-909", first_name="", last_name=data["last_name"], status=data["status"]),
    )
    monkeypatch.setattr(
        LeadService,
        "get_lead",
        lambda db, record_id: SimpleNamespace(id=record_id, first_name="", last_name="Kim", status="New"),
    )

    client.post(
        "/api/chat",
        json={
            "query": "create lead last name Kim status New",
            "conversation_id": conversation_id,
        },
    )

    follow_res = client.post(
        "/api/chat",
        json={
            "query": "방금 생성한 lead 보여줘",
            "conversation_id": conversation_id,
        },
    )
    follow_data = follow_res.json()

    assert follow_data["intent"] == "MANAGE"
    assert follow_data["record_id"] == "lead-909"
    assert follow_data["chat_card"]["mode"] == "view"


def test_explicit_manage_edit_request_opens_inline_edit_form(client, monkeypatch):
    conversation_id = "conv-memory-10"
    ConversationContextStore.clear(conversation_id)

    async def fake_llm(user_query: str, system_prompt: str):
        raise AssertionError("LLM should not be called for explicit manage edit request")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fake_llm)
    monkeypatch.setattr(
        LeadService,
        "get_lead",
        lambda db, record_id: SimpleNamespace(id=record_id, first_name="Ji", last_name="Han", status="Working"),
    )

    res = client.post(
        "/api/chat",
        json={
            "query": "Manage lead lead-1001 edit",
            "conversation_id": conversation_id,
        },
    )
    data = res.json()

    assert data["intent"] == "OPEN_FORM"
    assert data["record_id"] == "lead-1001"
    assert data["form_url"] == "/leads/new-modal?id=lead-1001"
