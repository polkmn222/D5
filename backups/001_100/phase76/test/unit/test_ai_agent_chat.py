import pytest
from fastapi.testclient import TestClient

from ai_agent.backend.main import app as ai_agent_app
from ai_agent.backend.service import AiAgentService


@pytest.fixture
def client():
    return TestClient(ai_agent_app)


def test_chat_requires_query(client):
    """홈탭 Ask AI Agent 버튼 - query 없이 호출 시 기본 안내 메시지 반환"""
    response = client.post("/api/chat", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "CHAT"
    assert "Please provide a query" in data["text"]


def test_chat_uses_highest_score_from_ensemble(client, monkeypatch):
    """여러 모델 응답 중 score가 가장 높은 결과를 선택하는지 검증"""

    async def fake_ensemble(user_query: str, system_prompt: str):
        return {
            "intent": "CHAT",
            "text": "Best answer",
            "score": 0.9,
        }

    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        fake_ensemble,
    )

    response = client.post("/api/chat", json={"query": "안녕하세요"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "CHAT"
    assert data["text"] == "Best answer"


def test_chat_no_api_keys_configured(client, monkeypatch):
    """API Key가 없을 경우 fallback 메시지 확인"""

    async def fake_ensemble(user_query: str, system_prompt: str):
        return {"intent": "CHAT", "text": "No AI API Keys configured."}

    monkeypatch.setattr(
        AiAgentService,
        "_call_multi_llm_ensemble",
        fake_ensemble,
    )

    response = client.post("/api/chat", json={"query": "테스트"})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "CHAT"
    assert "No AI API Keys" in data["text"]
