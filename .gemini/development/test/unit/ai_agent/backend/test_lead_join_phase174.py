import pytest
import sys
import os

# Adjust path to import AiAgentService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
from ai_agent.ui.backend.service import AiAgentService

def test_lead_default_query_parts_contains_joins():
    """Verify that lead queries include model JOIN and display_name concatenation."""
    parts = AiAgentService._default_query_parts("lead")
    assert parts is not None
    assert "l.first_name || ' ' || l.last_name AS display_name" in parts["select"]
    assert "m.name AS model" in parts["select"]
    assert "leads l" in parts["from"]
    assert "LEFT JOIN models m ON l.model = m.id" in parts["from"]
    assert "l.deleted_at IS NULL" in parts["where"]

def test_lead_search_alias():
    """Verify that search applies 'l.' aliases for leads."""
    parts = AiAgentService._default_query_parts("lead")
    search_sql = AiAgentService._apply_search_to_sql("lead", parts, "Test")
    assert "l.first_name ILIKE '%Test%'" in search_sql["where"]
    assert "l.last_name ILIKE '%Test%'" in search_sql["where"]
    assert "l.status ILIKE '%Test%'" in search_sql["where"]
