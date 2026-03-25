"""
Unit tests for Phase 173: API Key Removal Verification.
Tests verify:
1. Multi-LLM Ensemble no longer calls Gemini or OpenAI.
2. USAGE intent response reflects only Cerebras and Groq.
3. System still functions with Cerebras/Groq.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from ai_agent.ui.backend.service import AiAgentService

class TestApiKeyRemovalPhase173:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_ensemble_excludes_gemini_openai(self):
        """Ensemble should ONLY attempt to call Cerebras and Groq."""
        # Setup mocks for all 4 possible providers
        with patch("ai_agent.ui.backend.service.AiAgentService._call_cerebras", new_callable=AsyncMock) as mock_cerebras, \
             patch("ai_agent.ui.backend.service.AiAgentService._call_groq", new_callable=AsyncMock) as mock_groq:
            
            # We don't even need to mock _call_gemini/_call_openai because they should be GONE from the class
            # and not even referenced in the ensemble logic.
            
            # Mock API keys as if they are all set
            with patch("ai_agent.ui.backend.service.CEREBRAS_API_KEY", "test_cerebras"), \
                 patch("ai_agent.ui.backend.service.GROQ_API_KEY", "test_groq"):
                
                # We want to check that gemini/openai aren't even checked or called
                # In the new code, the variables GEMINI_API_KEY and OPENAI_API_KEY are no longer used in the ensemble.
                
                # Mock return values
                mock_cerebras.return_value = {"intent": "CHAT", "score": 0.9, "text": "Cerebras response"}
                mock_groq.return_value = {"intent": "CHAT", "score": 0.8, "text": "Groq response"}
                
                result = self._run(AiAgentService._call_multi_llm_ensemble("hi", "system prompt"))
                
                # Verify only the active ones were called
                mock_cerebras.assert_called_once()
                mock_groq.assert_called_once()
                
                # Ensure it picked the best score (Cerebras)
                assert result["text"] == "Cerebras response"

    def test_usage_intent_updates(self):
        """USAGE intent should only list Cerebras and Groq."""
        db = MagicMock()
        agent_output = {"intent": "USAGE"}
        
        result = self._run(AiAgentService._execute_intent(db, agent_output, "usage"))
        
        text = result.get("text", "")
        assert "two different AI providers" in text
        assert "Cerebras" in text
        assert "Groq" in text
        assert "Gemini" not in text
        assert "OpenAI" not in text

    def test_variable_existence(self):
        """Verify that GEMINI_API_KEY and OPENAI_API_KEY are no longer used in ensemble logic."""
        import inspect
        source = inspect.getsource(AiAgentService._call_multi_llm_ensemble)
        assert "GEMINI_API_KEY" not in source
        assert "OPENAI_API_KEY" not in source
        assert "_call_gemini" not in source
        assert "_call_openai" not in source
