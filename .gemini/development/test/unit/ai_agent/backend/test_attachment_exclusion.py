import pytest
import asyncio
from unittest.mock import MagicMock

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
from ai_agent.ui.backend.service import AiAgentService

@pytest.mark.asyncio
async def test_attachment_exclusion():
    """Verify that queries containing 'attachment' are rejected by the AI Agent."""
    mock_db = MagicMock()
    
    # Test raw attachment mention
    response1 = await AiAgentService.process_query(mock_db, "search attachment for contract")
    assert response1["intent"] == "CHAT"
    assert "cannot query or manage attachments" in response1["text"]
    
    # Test conversational attachment request
    response2 = await AiAgentService.process_query(mock_db, "show me the latest attachments")
    assert response2["intent"] == "CHAT"
    assert "cannot query or manage attachments" in response2["text"]
    
    # Ensure regular queries still pass (intent resolution returns something else, but mock_db will fail or succeed)
    # We will mock _execute_intent to just return a dummy
    AiAgentService._execute_intent = AsyncMockResponse({"intent": "QUERY", "object_type": "lead"})
    
    response3 = await AiAgentService.process_query(mock_db, "search lead for john")
    assert response3["intent"] == "QUERY"

# Helper for async mock
class AsyncMockResponse:
    def __init__(self, response):
        self.response = response
    async def __call__(self, *args, **kwargs):
        return self.response
