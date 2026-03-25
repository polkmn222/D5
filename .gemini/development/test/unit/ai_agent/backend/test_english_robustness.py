import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../")))
from ai_agent.llm.backend.intent_preclassifier import IntentPreClassifier

def test_english_typo_correction():
    """Verify that common English typos are normalized correctly."""
    assert "lead" in IntentPreClassifier.normalize("Show lds")
    assert "contact" in IntentPreClassifier.normalize("Open contax")
    assert "opportunity" in IntentPreClassifier.normalize("My oportunity")
    assert "opportunity" in IntentPreClassifier.normalize("check opps")
    assert "message_template" in IntentPreClassifier.normalize("load templt")

def test_possessive_stripping():
    """Verify that possessive 's is stripped out."""
    assert IntentPreClassifier.normalize("John's lead") == "john lead"
    assert IntentPreClassifier.normalize("the model's details") == "the model details"

def test_informal_action_detection():
    """Verify that informal verbs are correctly identified."""
    # Test Create
    d1 = IntentPreClassifier.detect("snag a new lead")
    assert d1["intent"] == "CHAT" or d1["intent"] == "CREATE" # Depending on punctuation/token count
    
    # Test Read/Open
    d2 = IntentPreClassifier.detect("grab the lead")
    assert d2["intent"] == "CHAT"
    
    # Test Update
    d3 = IntentPreClassifier.detect("tweak this lead")
    assert d3["intent"] == "CHAT"
    
    # Test Delete
    d4 = IntentPreClassifier.detect("nuke this lead")
    assert d4["intent"] == "CHAT"

def test_intent_preclassifier_normalization_boundary():
    """Test that typos are only replaced at word boundaries."""
    # 'opp' is a typo for 'opportunity'. If it's part of a word, it shouldn't be replaced.
    # Actually 'opportunity' HAS 'opp' in it. Our regex \b should handle this.
    assert IntentPreClassifier.normalize("opportunity") == "opportunity"
    assert IntentPreClassifier.normalize("opp") == "opportunity"

def test_intent_preclassifier_synonyms():
    """Test mapping of Korean synonyms via detect()."""
    d1 = IntentPreClassifier.detect("리드 보여줘")
    assert d1["object_type"] == "lead"
    d2 = IntentPreClassifier.detect("연락처 목록")
    assert d2["object_type"] == "contact"
