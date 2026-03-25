import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost/d4_test")

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from db.models import Lead, Opportunity
from web.backend.app.services.search_service import SearchService

class FakeQuery:
    def __init__(self, rows):
        self.rows = list(rows)
        self.filtered_rows = list(rows)
        self.limit_value = None

    def _collect_terms(self, condition):
        terms = []
        right = getattr(condition, "right", None)
        value = getattr(right, "value", None)
        if isinstance(value, str):
            terms.append(value.replace("%", "").lower())
        for child in getattr(condition, "get_children", lambda: [])():
            terms.extend(self._collect_terms(child))
        return terms

    def filter(self, *args):
        terms = []
        for condition in args:
            terms.extend(self._collect_terms(condition))

        terms = [term for term in terms if term]
        if terms:
            self.filtered_rows = [
                row
                for row in self.rows
                if any(
                    term in str(value).lower()
                    for term in terms
                    for value in row.__dict__.values()
                    if value is not None
                )
            ]
        return self

    def limit(self, limit_value):
        self.limit_value = limit_value
        return self

    def all(self):
        rows = self.filtered_rows
        if self.limit_value is None:
            return list(rows)
        return list(rows[: self.limit_value])


class FakeDB:
    def __init__(self, mapping):
        self.mapping = mapping

    def query(self, model):
        return FakeQuery(self.mapping.get(model, []))


def make_db():
    return FakeDB(
        {
            Lead: [
                SimpleNamespace(id="L1", first_name="Alice", last_name="Alpha", email="alice@example.com", phone=None),
                SimpleNamespace(id="L2", first_name="Alex", last_name="Abbot", email="alex@example.com", phone=None),
            ],
            Opportunity: [
                SimpleNamespace(id="O1", name="Alpha Project", stage="Prospecting"),
            ],
        }
    )

def test_search_suggestions_limit():
    db = make_db()
    results = SearchService.global_search(db, "Al", scope="all", limit=1)

    lead_count = len([r for r in results if r["type"] == "Lead"])
    opp_count = len([r for r in results if r["type"] == "Opportunity"])

    assert lead_count <= 1
    assert opp_count <= 1

def test_suggestion_format():
    db = make_db()
    results = SearchService.global_search(db, "Alice", scope="all", limit=5)
    assert len(results) > 0
    item = results[0]
    assert "name" in item
    assert "type" in item
    assert "url" in item
    assert "info" in item
