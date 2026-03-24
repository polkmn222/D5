import pytest
from fastapi.testclient import TestClient

from ai_agent.backend.main import app as ai_agent_app
from ai_agent.backend.service import AiAgentService


@pytest.fixture
def client():
    return TestClient(ai_agent_app)


# -------------------------------
# Multi-object Ambiguity Tests
# -------------------------------

@pytest.mark.parametrize("query", [
    "리드랑 기회 보여줘",
    "lead and contact",
    "contact opportunity list",
])
def test_multi_object_should_trigger_clarification(client, monkeypatch, query):
    async def fake_llm(user_query: str, system_prompt: str):
        # If reasoner fails, this would be returned instead
        return {"intent": "QUERY", "object_type": "lead", "score": 0.5}

    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        fake_llm,
    )

    res = client.post("/api/chat", json={"query": query})
    data = res.json()

    assert data["intent"] == "CHAT"
    assert "which" in data["text"].lower() or "어떤" in data["text"]


# -------------------------------
# Complex Condition Fallback
# -------------------------------

@pytest.mark.parametrize("query", [
    "이번주 생성된 리드 보여줘",
    "show leads created this week",
    "status가 new인 리드 보여줘",
    "lead where status = new",
])
def test_complex_queries_should_not_use_rule(client, monkeypatch, query):
    async def fake_llm(user_query: str, system_prompt: str):
        return {"intent": "QUERY", "object_type": "lead", "score": 0.9}

    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        fake_llm,
    )

    res = client.post("/api/chat", json={"query": query})
    data = res.json()

    # Should come from LLM mock, not rule
    assert data["intent"] == "QUERY"
    assert data["object_type"] == "lead"


# -------------------------------
# Single Word Safe Handling
# -------------------------------

@pytest.mark.parametrize("query, expected_object", [
    ("lead", "lead"),
    ("리드", "lead"),
    ("contact", "contact"),
    ("기회", "opportunity"),
])
def test_single_word_queries_are_safe_query(client, monkeypatch, query, expected_object):
    async def fake_llm(user_query: str, system_prompt: str):
        return {"intent": "CHAT", "score": 0.3}

    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        fake_llm,
    )

    res = client.post("/api/chat", json={"query": query})
    data = res.json()

    assert data["intent"] == "QUERY"
    assert data["object_type"] == expected_object


# -------------------------------
# Ambiguous Action Handling
# -------------------------------

@pytest.mark.parametrize("query", [
    "리드 만들고 보여줘",
    "create and show lead",
])
def test_multiple_actions_should_trigger_clarification(client, monkeypatch, query):
    async def fake_llm(user_query: str, system_prompt: str):
        return {"intent": "CREATE", "object_type": "lead", "score": 0.6}

    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        fake_llm,
    )

    res = client.post("/api/chat", json={"query": query})
    data = res.json()

    assert data["intent"] == "CHAT"
    assert "clarify" in data["text"].lower() or "어떤" in data["text"]
