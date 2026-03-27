
import pytest
from ai_agent.llm.backend.intent_preclassifier import IntentPreClassifier

def test_create_lead_preclassification():
    res = IntentPreClassifier.detect("create lead")
    assert res is not None
    assert res["intent"] == "OPEN_FORM"
    assert res["object_type"] == "lead"
    assert res["form_url"] == "/leads/new-modal"

def test_create_message_template_preclassification():
    res = IntentPreClassifier.detect("create template")
    assert res is not None
    assert res["intent"] == "OPEN_FORM"
    assert res["object_type"] == "message_template"
    assert res["form_url"] == "/message_templates/new-modal"

def test_complex_create_goes_to_llm():
    # Should return None because it contains field hints (email), 
    # meaning it might have data to process via LLM
    res = IntentPreClassifier.detect("create lead with email test@test.com")
    assert res is None

def test_edit_lead_no_id_suggests_selection():
    res = IntentPreClassifier.detect("edit lead")
    assert res is not None
    assert res["intent"] == "CHAT"
    assert "select it" in res["text"]

def test_normalize_object_type_handles_aliases():
    assert IntentPreClassifier.normalize_object_type("contacts") == "contact"
    assert IntentPreClassifier.normalize_object_type("message template") == "message_template"
    assert IntentPreClassifier.normalize_object_type("unknown-object") is None


def test_detect_object_mentions_returns_distinct_objects():
    assert IntentPreClassifier.detect_object_mentions("show lead and contact") == ["lead", "contact"]
    assert IntentPreClassifier.detect_object_mentions("templates") == ["message_template"]

if __name__ == "__main__":
    pytest.main([__file__])
