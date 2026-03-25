import os
import sys
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost/d4_test")

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from db.models import Lead, Opportunity, Contact, Model
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
        rows = list(self.filtered_rows)
        if self.limit_value is not None:
            rows = rows[: self.limit_value]
        return rows


class FakeDB:
    def __init__(self, mapping):
        self.mapping = mapping

    def query(self, model):
        return FakeQuery(self.mapping.get(model, []))


def make_db():
    return FakeDB(
        {
            Lead: [SimpleNamespace(id="L1", first_name="John", last_name="Doe", email="john@example.com", phone=None)],
            Contact: [SimpleNamespace(id="C1", name="Jane Smith", first_name=None, last_name=None, email="jane@example.com", phone=None)],
            Opportunity: [SimpleNamespace(id="O1", name="Big Deal", stage="Prospecting")],
            Model: [SimpleNamespace(id="M1", name="Model X", description="Luxury SUV")],
        }
    )

def test_search_all():
    db = make_db()
    results = SearchService.global_search(db, "John", scope="all")
    assert len(results) == 1
    assert results[0]["type"] == "Lead"

    results = SearchService.global_search(db, "Deal", scope="all")
    assert len(results) == 1
    assert results[0]["type"] == "Opportunity"

def test_scoped_search_lead():
    db = make_db()
    results = SearchService.global_search(db, "John", scope="lead")
    assert len(results) == 1
    assert results[0]["type"] == "Lead"

    results = SearchService.global_search(db, "John", scope="opportunity")
    assert len(results) == 0

def test_scoped_search_model():
    db = make_db()
    results = SearchService.global_search(db, "Model", scope="model")
    assert len(results) == 1
    assert results[0]["type"] == "Model"
    assert results[0]["name"] == "Model X"

def test_case_insensitivity():
    db = make_db()
    results = SearchService.global_search(db, "john", scope="all")
    assert len(results) == 1
    assert results[0]["name"] == "John Doe"

def test_empty_query():
    db = make_db()
    results = SearchService.global_search(db, "", scope="all")
    assert len(results) == 0
