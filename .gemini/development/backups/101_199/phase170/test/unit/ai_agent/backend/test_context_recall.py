import pytest
import asyncio
from unittest.mock import MagicMock

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
from ai_agent.backend.service import AiAgentService
from ai_agent.backend.conversation_context import ConversationContextStore

def test_contextual_pronoun_resolution():
    """Verify that 'it', 'them', 'that one' correctly resolve to the last object."""
    conv_id = "test_conv_pronoun"
    ConversationContextStore.clear(conv_id)
    
    # 1. Establish context (Show leads) WITH a record_id
    ConversationContextStore.remember_object(conv_id, "lead", "QUERY", record_id="L-1001")
    
    # 2. Ask to "update it"
    result = AiAgentService._resolve_contextual_record_reference("update it", conv_id)
    assert result is not None
    assert result["intent"] == "MANAGE"
    assert result["object_type"] == "lead"
    assert result["record_id"] == "L-1001"
    
    # 3. Test "them"
    result_them = AiAgentService._resolve_contextual_record_reference("show them", conv_id)
    assert result_them["object_type"] == "lead"

def test_informal_delete_confirmation():
    """Verify that 'nuke' or 'dump' triggers delete confirmation logic."""
    conv_id = "test_conv_nuke"
    ConversationContextStore.clear(conv_id)
    
    # 1. Establish context
    ConversationContextStore.remember_object(conv_id, "opportunity", "CHAT", record_id="opp_123")
    
    # 2. "Nuke it"
    result = AiAgentService._resolve_delete_confirmation("nuke it", conv_id)
    assert result is not None
    assert result["intent"] == "CHAT"
    assert "permanently delete" in result["text"]
    assert result["object_type"] == "opportunity"
    
    # 3. "No, dump it" (alternative informal)
    result_dump = AiAgentService._resolve_delete_confirmation("dump it", conv_id)
    assert result_dump is not None
    assert "permanently delete" in result_dump["text"]

def test_multi_turn_selection_delete():
    """Verify selection-based delete works with 'it'."""
    conv_id = "test_selection_it"
    ConversationContextStore.clear(conv_id)
    
    # 1. Set selection
    selection = {"object_type": "contact", "ids": ["c1"], "labels": ["John Doe"]}
    ConversationContextStore.remember_selection(conv_id, selection)
    
    # 2. "delete them"
    result = AiAgentService._resolve_delete_confirmation("delete them", conv_id, selection=selection)
    assert "John Doe" in result["text"]
    assert "permanently delete" in result["text"]
