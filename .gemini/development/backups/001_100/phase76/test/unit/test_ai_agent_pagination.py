import pytest

from ai_agent.backend.service import AiAgentService
from ai_agent.backend.recommendations import AIRecommendationService


class FakeRow:
    def __init__(self, mapping):
        self._mapping = mapping


class FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class FakeDB:
    def __init__(self, total, rows):
        self.total = total
        self.rows = rows
        self.queries = []

    def execute(self, sql):
        sql_text = str(sql)
        self.queries.append(sql_text)
        if "COUNT(*) AS total_count" in sql_text:
            return FakeScalarResult(self.total)
        return [FakeRow(row) for row in self.rows]


@pytest.mark.asyncio
async def test_query_results_include_pagination_metadata():
    db = FakeDB(
        total=120,
        rows=[{"id": "lead-51", "first_name": "A", "last_name": "Kim", "status": "New"}],
    )

    response = await AiAgentService._execute_intent(
        db,
        {"intent": "QUERY", "object_type": "lead"},
        "show all leads",
        conversation_id="conv-page-1",
        page=2,
        per_page=50,
    )

    assert response["intent"] == "QUERY"
    assert response["pagination"] == {
        "page": 2,
        "per_page": 50,
        "total": 120,
        "total_pages": 3,
        "object_type": "lead",
    }
    assert response["results"][0]["id"] == "lead-51"
    assert "LIMIT 50 OFFSET 50" in response["sql"]


def test_pagination_sanitizes_page_size_and_offset():
    page, per_page, offset = AiAgentService._sanitize_pagination(page=0, per_page=1000)

    assert page == 1
    assert per_page == 50
    assert offset == 0


class FakeRecommend:
    def __init__(self, idx):
        self.id = f"opp-{idx}"
        self.name = f"Opportunity {idx}"
        self.amount = idx * 1000
        self.stage = "Prospecting"
        self.temp_display = "Hot"


@pytest.mark.asyncio
async def test_recommend_results_include_pagination(monkeypatch):
    recommends = [FakeRecommend(idx) for idx in range(1, 76)]

    monkeypatch.setattr(AIRecommendationService, "get_ai_recommendations", lambda db, limit=10: recommends[:limit])

    response = await AiAgentService._execute_intent(
        db=None,
        agent_output={"intent": "RECOMMEND"},
        user_query="AI Recommend",
        page=2,
        per_page=50,
    )

    assert response["pagination"] == {
        "page": 2,
        "per_page": 50,
        "total": 75,
        "total_pages": 2,
        "object_type": "opportunity",
    }
    assert response["results"][0]["id"] == "opp-51"
    assert response["original_query"] == "AI Recommend"
