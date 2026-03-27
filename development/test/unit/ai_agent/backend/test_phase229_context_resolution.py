from ai_agent.llm.backend.conversation_context import ConversationContextStore
from ai_agent.ui.backend.service import AiAgentService


def test_contextual_reference_prefers_conversation_context_when_selection_absent():
    conv_id = "phase229-context-first"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_object(conv_id, "lead", "OPEN_RECORD", record_id="LEAD229A")

    result = AiAgentService._resolve_contextual_record_reference("open that record", conv_id)

    assert result is not None
    assert result["intent"] == "MANAGE"
    assert result["object_type"] == "lead"
    assert result["record_id"] == "LEAD229A"


def test_contextual_reference_uses_single_selected_record_when_context_missing():
    conv_id = "phase229-selection-fallback"
    ConversationContextStore.clear(conv_id)
    selection = {"object_type": "contact", "ids": ["CONTACT229A"], "labels": ["Ada Kim"]}

    result = AiAgentService._resolve_contextual_record_reference("edit this record", conv_id, selection)

    assert result is not None
    assert result["intent"] == "MANAGE"
    assert result["object_type"] == "contact"
    assert result["record_id"] == "CONTACT229A"


def test_contextual_reference_asks_for_clarification_when_context_and_selection_conflict():
    conv_id = "phase229-conflict"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_object(conv_id, "lead", "OPEN_RECORD", record_id="LEAD229B")
    selection = {"object_type": "opportunity", "ids": ["OPP229B"], "labels": ["Fleet Renewal"]}

    result = AiAgentService._resolve_contextual_record_reference("edit that", conv_id, selection)

    assert result is not None
    assert result["intent"] == "CHAT"
    assert "two different records" in result["text"]
    assert "LEAD229B" in result["text"]
    assert "OPP229B" in result["text"]


def test_contextual_reference_does_not_silently_cross_objects():
    conv_id = "phase229-object-mismatch"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_object(conv_id, "lead", "OPEN_RECORD", record_id="LEAD229C")

    result = AiAgentService._resolve_contextual_record_reference("edit that contact", conv_id)

    assert result is not None
    assert result["intent"] == "CHAT"
    assert result["object_type"] == "contact"
    assert "specific contact record" in result["text"]


def test_reasoning_context_includes_last_created_and_selection():
    conv_id = "phase229-reasoning-context"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_created(conv_id, "lead", "LEAD229D")
    ConversationContextStore.remember_selection(
        conv_id,
        {"object_type": "lead", "ids": ["LEAD229D"], "labels": ["Ada Kim"]},
    )

    result = ConversationContextStore.build_reasoning_context(conv_id)

    assert result["last_created"] == {"object_type": "lead", "record_id": "LEAD229D"}
    assert result["selection"]["object_type"] == "lead"
    assert result["selection"]["record_ids"] == ["LEAD229D"]
    assert result["selection"]["labels"] == ["Ada Kim"]


def test_reasoning_context_marks_selection_conflict():
    conv_id = "phase229-reasoning-conflict"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_object(conv_id, "lead", "MANAGE", record_id="LEAD229E")
    ConversationContextStore.remember_selection(
        conv_id,
        {"object_type": "contact", "ids": ["CONTACT229E"], "labels": ["Ben Park"]},
    )

    result = ConversationContextStore.build_reasoning_context(conv_id)

    assert result["safety"]["has_selection_conflict"] is True
    assert result["safety"]["has_multi_selection"] is False
