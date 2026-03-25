
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

if __name__ == "__main__":
    pytest.main([__file__])
