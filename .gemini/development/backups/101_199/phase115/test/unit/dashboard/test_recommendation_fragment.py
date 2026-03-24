from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient

from db.database import Base, engine
from web.backend.app.main import app
from ai_agent.backend.recommendations import AIRecommendationService


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
    assert ">New<" not in response.text


def test_dashboard_recommendation_mode_endpoint_updates_shared_mode():
    Base.metadata.create_all(bind=engine)
    original_mode = AIRecommendationService.get_recommendation_mode()

    try:
        with TestClient(app) as client:
            response = client.post("/api/recommendations/mode", json={"mode": "New Records"})

        assert response.status_code == 200
        assert response.json() == {"status": "success", "mode": "New Records"}
        assert AIRecommendationService.get_recommendation_mode() == "Default"
    finally:
        AIRecommendationService.set_recommendation_mode(original_mode)


def test_dashboard_template_contains_manual_recommend_mode_buttons():
    root = next(path for path in Path(__file__).resolve().parents if path.name == "development")
    html = (root / "web" / "frontend" / "templates" / "dashboard" / "dashboard.html").read_text()

    assert "data-ai-recommend-current-mode" in html
    assert "AI Recommend Mode: {{ recommendation_mode }}" in html
    assert html.count("data-ai-recommend-mode=") == 1
    assert "setDashboardRecommendationMode('{{ mode }}')" in html
    assert "['Hot Deals', 'Follow Up', 'Closing Soon', 'New Records']" in html
    assert "Start Recommend" in html
    assert "Choose one mode first" in html


def test_dashboard_recommendation_fragment_wraps_table_in_scroll_shell(monkeypatch):
    Base.metadata.create_all(bind=engine)
    fake_recommendations = [FakeOpp(f"opp-{idx}", f"Deal {idx}", idx * 1000, "Prospecting", "New") for idx in range(1, 9)]

    monkeypatch.setattr(
        "ai_agent.backend.recommendations.AIRecommendationService.get_sendable_recommendations",
        lambda db, limit=15, scan_limit=50: fake_recommendations,
    )
    monkeypatch.setattr(
        "web.backend.app.services.model_service.ModelService.get_model",
        lambda db, model_id: None,
    )

    with TestClient(app) as client:
        response = client.get("/api/recommendations")

    assert response.status_code == 200
    assert "dashboard-recommend-table-shell" in response.text
    assert response.text.count("/opportunities/") == 8
