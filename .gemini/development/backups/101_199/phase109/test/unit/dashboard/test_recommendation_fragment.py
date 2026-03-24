from datetime import datetime

from fastapi.testclient import TestClient

from db.database import Base, engine
from web.backend.app.main import app


class FakeOpp:
    def __init__(self, opp_id: str, name: str, amount: int, stage: str, temp_display: str):
        self.id = opp_id
        self.name = name
        self.amount = amount
        self.stage = stage
        self.temp_display = temp_display
        self.created_at = datetime(2026, 3, 23)
        self.model = None


def test_dashboard_recommendation_fragment_normalizes_temperatures(monkeypatch):
    Base.metadata.create_all(bind=engine)

    fake_recommendations = [
        FakeOpp("opp-hot", "Hot Deal", 1000, "Negotiation/Review", "Urgent"),
        FakeOpp("opp-warm", "Warm Deal", 2000, "Proposal/Price Quote", "Gold"),
        FakeOpp("opp-cold", "Cold Deal", 3000, "Prospecting", "New"),
    ]

    monkeypatch.setattr(
        "ai_agent.backend.recommendations.AIRecommendationService.get_sendable_recommendations",
        lambda db, limit=5, scan_limit=50: fake_recommendations,
    )
    monkeypatch.setattr(
        "web.backend.app.services.model_service.ModelService.get_model",
        lambda db, model_id: None,
    )

    with TestClient(app) as client:
        response = client.get("/api/recommendations")

    assert response.status_code == 200
    assert "🔥 Hot" in response.text
    assert "☀️ Warm" in response.text
    assert "❄️ Cold" in response.text
    assert "Urgent" not in response.text
    assert "Gold" not in response.text
    assert "New" not in response.text
