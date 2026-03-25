import pytest
from ai_agent.ui.backend.service import AiAgentService
from ai_agent.llm.backend.conversation_context import ConversationContextStore
import inspect

def test_force_delete_bypass_single_record():
    """Test that [FORCE_DELETE] bypasses the double confirmation for single record deletion"""
    ConversationContextStore.clear_pending_delete("test_conv")
    
    user_query = "[FORCE_DELETE] Delete lead 123e4567-e89b-12d3-a456-426614174000"
    
    result = AiAgentService._resolve_delete_confirmation(user_query, "test_conv", None)
    
    assert result is not None
    assert result.get("intent") == "DELETE"
    assert result.get("object_type") == "lead"
    assert result.get("record_id") == "123e4567-e89b-12d3-a456-426614174000"
    assert result.get("score") == 1.0


def test_force_delete_bypass_bulk_selection():
    """Test that [FORCE_DELETE] bypasses the double confirmation for bulk selection deletion"""
    ConversationContextStore.clear_pending_delete("test_conv")
    
    user_query = "[FORCE_DELETE] Delete selected lead records"
    selection = {
        "object_type": "lead",
        "ids": ["lead-1", "lead-2"],
        "labels": ["Lead One", "Lead Two"]
    }
    
    result = AiAgentService._resolve_delete_confirmation(user_query, "test_conv", selection)
    
    assert result is not None
    assert result.get("intent") == "DELETE"
    assert result.get("object_type") == "lead"
    # For bulk, it sets record_id to None if multiple
    assert result.get("record_id") is None
    assert result.get("selection") is not None
    assert result.get("selection")["ids"] == ["lead-1", "lead-2"]
    assert result.get("score") == 1.0

def test_system_prompt_contains_table_standards():
    """Test that Phase 183 table standard constraints are in the system prompt"""
    source = inspect.getsource(AiAgentService.process_query)
    assert "TRIM(CONCAT_WS(' ', first_name, last_name)) AS display_name" in source
    assert "JOIN with the `models` table to provide `model_name`" in source