import pytest
from datetime import datetime, timedelta
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
    AIRecommendationService.set_recommendation_mode("Follow Up")

    response = await AiAgentService._execute_intent(
        db=None,
        agent_output={"intent": "MODIFY_UI"},
        user_query="Change AI Recommend",
    )

    assert response["intent"] == "CHAT"
    assert "current **AI Recommend** logic is **Follow Up**" in response["text"]
    assert "[Follow Up (Current)]" in response["text"]
    assert "[Closed Won" in response["text"]


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

    assert response["text"].endswith("Current logic: **Closed Won**.")
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
    assert AIRecommendationService.user_facing_mode_label("Closing Soon") == "Closed Won"


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


def test_refresh_opportunity_temperatures_applies_hot_warm_cold_rules(monkeypatch):
    class FakeOpp:
        def __init__(self, stage, status, created_at):
            self.stage = stage
            self.status = status
            self.created_at = created_at
            self.temperature = None

    now = datetime.now()
    hot = FakeOpp("Test Drive", "Open", now)
    cold_old = FakeOpp("Prospecting", "Open", now - timedelta(days=31))
    cold_lost = FakeOpp("Prospecting", "Closed Lost", now)
    warm = FakeOpp("Prospecting", "Open", now)

    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = [hot, cold_old, cold_lost, warm]

    AIRecommendationService.refresh_opportunity_temperatures(db)

    assert hot.temperature == "Hot"
    assert cold_old.temperature == "Cold"
    assert cold_lost.temperature == "Cold"
    assert warm.temperature == "Warm"
    db.commit.assert_called_once()


def test_refresh_opportunity_temperatures_skips_repeat_same_day_ai_update():
    db = MagicMock()
    AIRecommendationService._ensure_opportunity_updated_by_column = MagicMock()
    AIRecommendationService._already_refreshed_today = MagicMock(return_value=True)

    AIRecommendationService.refresh_opportunity_temperatures(db)

    db.commit.assert_not_called()


def test_user_facing_mode_label_uses_closed_won_name():
    assert AIRecommendationService.user_facing_mode_label("Closing Soon") == "Closed Won"
