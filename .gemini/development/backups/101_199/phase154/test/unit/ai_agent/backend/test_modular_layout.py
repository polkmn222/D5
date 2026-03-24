from pathlib import Path

from ai_agent.backend.ai_service import AIService as LegacyAIService
from ai_agent.backend.conversation_context import ConversationContextStore as LegacyConversationContextStore
from ai_agent.backend.intent_preclassifier import IntentPreClassifier as LegacyIntentPreClassifier
from ai_agent.backend.intent_reasoner import IntentReasoner as LegacyIntentReasoner
from ai_agent.backend.recommendations import AIRecommendationService as LegacyRecommendationService
from ai_agent.backend.router import router as legacy_router
from ai_agent.backend.shell.chat_api import router as shell_router
from ai_agent.backend.shell.conversation_context import ConversationContextStore as ShellConversationContextStore
from ai_agent.backend.llm.intent_preclassifier import IntentPreClassifier as LlmIntentPreClassifier
from ai_agent.backend.llm.intent_reasoner import IntentReasoner as LlmIntentReasoner
from ai_agent.backend.llm.summary_service import AIService as ModularAIService
from ai_agent.backend.recommend.service import AIRecommendationService as ModularRecommendationService


ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
AI_AGENT_ROOT = ROOT / "ai_agent"


def test_legacy_backend_imports_bridge_to_modular_locations():
    assert LegacyConversationContextStore is ShellConversationContextStore
    assert LegacyIntentPreClassifier is LlmIntentPreClassifier
    assert LegacyIntentReasoner is LlmIntentReasoner
    assert LegacyAIService is ModularAIService
    assert LegacyRecommendationService is ModularRecommendationService
    assert legacy_router is shell_router


def test_feature_first_backend_directories_exist():
    expected_paths = [
        AI_AGENT_ROOT / "backend" / "shell" / "app.py",
        AI_AGENT_ROOT / "backend" / "shell" / "chat_api.py",
        AI_AGENT_ROOT / "backend" / "shell" / "conversation_context.py",
        AI_AGENT_ROOT / "backend" / "llm" / "intent_preclassifier.py",
        AI_AGENT_ROOT / "backend" / "llm" / "intent_reasoner.py",
        AI_AGENT_ROOT / "backend" / "llm" / "summary_service.py",
        AI_AGENT_ROOT / "backend" / "recommend" / "service.py",
        AI_AGENT_ROOT / "backend" / "objects" / "lead" / "cards.py",
        AI_AGENT_ROOT / "backend" / "objects" / "lead" / "forms.py",
        AI_AGENT_ROOT / "backend" / "objects" / "lead" / "memory.py",
    ]
    for path in expected_paths:
        assert path.exists(), f"Missing modular backend path: {path}"
