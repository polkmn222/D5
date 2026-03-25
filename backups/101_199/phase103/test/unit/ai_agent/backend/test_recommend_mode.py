import pytest

from ai_agent.backend.recommendations import AIRecommendationService
from ai_agent.backend.service import AiAgentService


class FakeRecommend:
    def __init__(self, idx):
        self.id = f"opp-{idx}"
        self.name = f"Opportunity {idx}"
        self.amount = idx * 1000
        self.stage = "Prospecting"
        self.temp_display = "Hot"


@pytest.mark.asyncio
async def test_modify_ui_prompt_includes_current_recommend_mode(monkeypatch):
    AIRecommendationService.set_recommendation_mode("High Value")

    response = await AiAgentService._execute_intent(
        db=None,
        agent_output={"intent": "MODIFY_UI"},
        user_query="Change AI Recommend",
    )

    assert response["intent"] == "CHAT"
    assert "current **AI Recommend** logic is **High Value**" in response["text"]
    assert "[High Value (Current)]" in response["text"]


@pytest.mark.asyncio
async def test_recommend_response_includes_current_mode(monkeypatch):
    AIRecommendationService.set_recommendation_mode("Closing Soon")
    recommends = [FakeRecommend(idx) for idx in range(1, 4)]
    monkeypatch.setattr(AIRecommendationService, "get_ai_recommendations", lambda db, limit=10: recommends)

    response = await AiAgentService._execute_intent(
        db=None,
        agent_output={"intent": "RECOMMEND"},
        user_query="AI Recommend",
        page=1,
        per_page=50,
    )

    assert response["text"].endswith("Current logic: **Closing Soon**.")
    assert len(response["results"]) == 3
