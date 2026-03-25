import pytest
from fastapi.testclient import TestClient

from ai_agent.backend.main import app as ai_agent_app
from ai_agent.backend.service import AiAgentService
from web.backend.app.services.lead_service import LeadService


@pytest.fixture
def client():
    return TestClient(ai_agent_app)


# ---------- Helper Mock ----------

def mock_ensemble_factory(expected_intent, expected_object):
    async def _mock(user_query: str, system_prompt: str):
        return {
            "intent": expected_intent,
            "object_type": expected_object,
            "text": "mocked",
            "score": 0.85,
        }
    return _mock


# ---------- CREATE Start Variations (EN + KR) ----------

@pytest.mark.parametrize("query", [
    "리드 만들고 싶어",
    "리드를 만들어줘",
    "create lead",
    "I want to create lead",
    "I want to create laed",  # typo
])
def test_create_lead_variations(client, monkeypatch, query):
    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        mock_ensemble_factory("CREATE", "lead"),
    )
    res = client.post("/api/chat", json={"query": query})
    data = res.json()
    assert data["intent"] == "CHAT"
    assert data["object_type"] == "lead"
    assert "create a lead" in data["text"].lower()
    assert "last name" in data["text"].lower()


@pytest.mark.parametrize("query, obj", [
    ("create contact", "contact"),
    ("연락처 만들어줘", "contact"),
    ("create opportunity", "opportunity"),
    ("기회 생성", "opportunity"),
    ("create product", "product"),
    ("상품 추가", "product"),
    ("create asset", "asset"),
    ("자산 등록", "asset"),
    ("create brand", "brand"),
    ("브랜드 생성", "brand"),
    ("create model", "model"),
    ("모델 추가", "model"),
])
def test_create_all_objects(client, monkeypatch, query, obj):
    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        mock_ensemble_factory("CREATE", obj),
    )
    res = client.post("/api/chat", json={"query": query})
    data = res.json()
    assert data["intent"] == "CHAT"
    assert data["object_type"] == obj
    assert "please provide" in data["text"].lower()


def test_create_phrase_does_not_execute_create_immediately(client, monkeypatch):
    def fail_create(*args, **kwargs):
        raise AssertionError("create_lead should not be called for a simple create phrase")

    monkeypatch.setattr(LeadService, "create_lead", fail_create)

    res = client.post("/api/chat", json={"query": "create lead"})
    data = res.json()

    assert data["intent"] == "CHAT"
    assert data["object_type"] == "lead"


# ---------- QUERY Variations ----------

@pytest.mark.parametrize("query", [
    "show all lead",
    "all lead",
    "리드 전체 보여줘",
    "리드 목록",
])
def test_query_lead_variations(client, monkeypatch, query):
    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        mock_ensemble_factory("QUERY", "lead"),
    )
    res = client.post("/api/chat", json={"query": query})
    data = res.json()
    assert data["intent"] == "QUERY"
    assert data["object_type"] == "lead"


@pytest.mark.parametrize("query, obj", [
    ("all contacts", "contact"),
    ("연락처 전체", "contact"),
    ("show opportunities", "opportunity"),
    ("기회 목록", "opportunity"),
    ("all products", "product"),
    ("상품 전체", "product"),
    ("all assets", "asset"),
    ("자산 목록", "asset"),
])
def test_query_all_objects(client, monkeypatch, query, obj):
    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        mock_ensemble_factory("QUERY", obj),
    )
    res = client.post("/api/chat", json={"query": query})
    data = res.json()
    assert data["intent"] == "QUERY"
    assert data["object_type"] == obj


# ---------- Short / Ambiguous Commands ----------

@pytest.mark.parametrize("query, intent, obj", [
    ("lead", "QUERY", "lead"),
    ("리드", "QUERY", "lead"),
    ("contact", "QUERY", "contact"),
    ("기회", "QUERY", "opportunity"),
])
def test_short_single_word_commands(client, monkeypatch, query, intent, obj):
    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        mock_ensemble_factory(intent, obj),
    )
    res = client.post("/api/chat", json={"query": query})
    data = res.json()
    assert data["intent"] == intent
    assert data["object_type"] == obj


def test_rule_based_contact_query_returns_summary_text(client, monkeypatch):
    async def fail_llm(*args, **kwargs):
        raise AssertionError("LLM fallback should not run for simple contact list queries")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)

    res = client.post("/api/chat", json={"query": "Show all Contacts"})
    data = res.json()

    assert data["intent"] == "QUERY"
    assert data["object_type"] == "contact"
    assert data["text"].startswith("I ")
    assert "contact" in data["text"].lower()


@pytest.mark.parametrize("query, obj", [
    ("최근 생성 된 리드를 보여줘", "lead"),
    ("최근 생성 된 리드 보여줘", "lead"),
    ("최근 생성 된 연락처를 보여줘", "contact"),
])
def test_recently_created_korean_queries_match_query_intent(client, monkeypatch, query, obj):
    async def fail_llm(*args, **kwargs):
        raise AssertionError("LLM fallback should not run for recently created list queries")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)

    res = client.post("/api/chat", json={"query": query})
    data = res.json()

    assert data["intent"] == "QUERY"
    assert data["object_type"] == obj


def test_send_message_without_selection_respects_korean_language_preference(client, monkeypatch):
    async def fail_llm(*args, **kwargs):
        raise AssertionError("LLM fallback should not run for guided send message prompt")

    monkeypatch.setattr(AiAgentService, "_call_multi_llm_ensemble", fail_llm)

    res = client.post("/api/chat", json={"query": "Send Message", "language_preference": "kor"})
    data = res.json()

    assert data["intent"] == "CHAT"
    assert "누구에게 메시지를 보낼까요" in data["text"]
