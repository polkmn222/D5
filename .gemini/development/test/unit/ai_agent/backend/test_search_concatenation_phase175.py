import pytest
import sys
import os

# Adjust path to import AiAgentService
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
from ai_agent.ui.backend.service import AiAgentService

def test_search_fields_concatenation_lead():
    """Verify that lead search includes concatenated name field for LIKE matching."""
    parts = AiAgentService._default_query_parts("lead")
    search_sql = AiAgentService._apply_search_to_sql("lead", parts, "Test User")
    
    # Combined name search should be present
    assert "l.first_name || ' ' || l.last_name ILIKE '%Test User%'" in search_sql["where"]
    # Individual fields should also be present
    assert "l.first_name ILIKE '%Test User%'" in search_sql["where"]
    assert "l.last_name ILIKE '%Test User%'" in search_sql["where"]

def test_search_fields_concatenation_contact():
    """Verify that contact search includes concatenated name field."""
    parts = AiAgentService._default_query_parts("contact")
    search_sql = AiAgentService._apply_search_to_sql("contact", parts, "John Doe")
    
    assert "first_name || ' ' || last_name ILIKE '%John Doe%'" in search_sql["where"]
