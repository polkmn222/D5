import pytest
from unittest.mock import MagicMock

# Import the service directly rather than routing through the app to maintain isolated testing
# No need to import get_db, testing static methods
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
from ai_agent.ui.backend.service import AiAgentService

def test_opportunity_default_query_parts_contains_joins():
    """Verify that opportunity queries include contact and model JOINs."""
    parts = AiAgentService._default_query_parts("opportunity")
    assert parts is not None
    assert "LEFT JOIN contacts c" in parts["from"], "Missing Contact JOIN"
    assert "LEFT JOIN models m" in parts["from"], "Missing Model JOIN"
    assert "c.first_name || ' ' || c.last_name AS contact_display_name" in parts["select"]
    assert "c.phone AS contact_phone" in parts["select"]
    assert "m.name AS model_name" in parts["select"]
    assert "search_fields" not in parts  # just verifying parts structure

def test_opportunity_search_alias():
    """Verify that search applies 'o.name' instead of ambiguous 'name'."""
    parts = AiAgentService._default_query_parts("opportunity")
    search_sql = AiAgentService._apply_search_to_sql("opportunity", parts, "Test")
    assert "o.name ILIKE '%Test%'" in search_sql["where"], "Missing table alias in search"
    assert "o.stage" in search_sql["where"]
