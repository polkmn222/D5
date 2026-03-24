import pytest
from unittest.mock import MagicMock

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


@pytest.mark.asyncio
async def test_modify_ui_default_mode_copy_explains_recent_sendable_deals():
    response = await AiAgentService._execute_intent(
        db=None,
        agent_output={"intent": "MODIFY_UI"},
        user_query="Change AI Recommend Default",
    )

    assert response["text"]
    assert "New Records" in response["text"]
    assert "Most recently created sendable deals" in response["text"]


def test_user_facing_mode_label_uses_new_records_name():
    assert AIRecommendationService.user_facing_mode_label("Default") == "New Records"
    assert AIRecommendationService.user_facing_mode_label("Hot Deals") == "Hot Deals"


def test_temperature_labels_are_normalized_to_hot_warm_cold():
    assert AIRecommendationService.normalize_temperature_label("Urgent") == "Hot"
    assert AIRecommendationService.normalize_temperature_label("Gold") == "Warm"
    assert AIRecommendationService.normalize_temperature_label("New") == "Cold"
    assert AIRecommendationService.normalize_temperature_label("Warm") == "Warm"


def test_sendable_recommendations_skip_missing_phone_and_model(monkeypatch):
    class FakeOpp:
        def __init__(self, opp_id, contact, model):
            self.id = opp_id
            self.contact = contact
            self.model = model

    db = MagicMock()
    contact_query_one = MagicMock()
    contact_query_one.filter.return_value.first.return_value = type("Contact", (), {"phone": None})()
    contact_query_two = MagicMock()
    contact_query_two.filter.return_value.first.return_value = type("Contact", (), {"phone": "01011112222"})()
    model_query = MagicMock()
    model_query.filter.return_value.first.return_value = type("Model", (), {"id": "m-ready"})()

    db.query.side_effect = [contact_query_one, contact_query_two, model_query]

    monkeypatch.setattr(
        AIRecommendationService,
        "get_ai_recommendations",
        lambda db, limit=50: [
            FakeOpp("opp-1", "c-no-phone", "m-ready"),
            FakeOpp("opp-2", "c-ready", None),
            FakeOpp("opp-3", "c-ready", "m-ready"),
        ],
    )

    results = AIRecommendationService.get_sendable_recommendations(db, limit=5, scan_limit=50)

    assert [opp.id for opp in results] == ["opp-3"]
