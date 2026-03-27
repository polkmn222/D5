from unittest.mock import AsyncMock, patch

import pytest

from ai_agent.llm.backend.conversation_context import ConversationContextStore
from ai_agent.llm.backend.intent_reasoner import IntentReasoner
from ai_agent.ui.backend.service import AiAgentService


def _context(
    *,
    last_created=None,
    last_record=None,
    selection=None,
    query_results=None,
    safety=None,
):
    return {
        "last_created": dict(last_created or {}),
        "last_record": dict(last_record or {}),
        "selection": {
            "object_type": None,
            "record_ids": [],
            "labels": [],
            "count": 0,
            **(selection or {}),
        },
        "query_results": {
            "object_type": None,
            "results": [],
            "count": 0,
            **(query_results or {}),
        },
        **({"safety": dict(safety)} if safety else {}),
    }


def _validated(raw_output, user_query, reasoning_context):
    return IntentReasoner.validate_reasoning_output(raw_output, user_query, reasoning_context)


def _assert_chat_clarification(result, *snippets, confidence_band=None):
    assert result["intent"] == "CHAT"
    if confidence_band is not None:
        assert result["reasoning"]["confidence_band"] == confidence_band
    for snippet in snippets:
        assert snippet in result["text"]


def _assert_executable_result(result, *, intent, object_type=None, record_id=None, confidence_band=None):
    assert result["intent"] == intent
    if object_type is not None:
        assert result["object_type"] == object_type
    if record_id is not None:
        assert result["record_id"] == record_id
    if confidence_band is not None:
        assert result["reasoning"]["confidence_band"] == confidence_band


# Prompt Guidance Regression Proof


def test_build_reasoning_prompt_explicitly_distinguishes_intent_and_action():
    prompt = IntentReasoner.build_reasoning_prompt(
        metadata='{"tables": []}',
        language_preference="eng",
        reasoning_context={"last_record": {"object_type": "lead", "record_id": "LEAD-P1"}},
    )

    assert "`intent` is the validator-facing decision" in prompt
    assert "`action` must match `intent`" in prompt


def test_build_reasoning_prompt_explicitly_requires_clarification_for_unsafe_targets():
    prompt = IntentReasoner.build_reasoning_prompt(
        metadata='{"tables": []}',
        language_preference="eng",
        reasoning_context={"selection": {"object_type": "lead", "record_ids": ["LEAD-P2"], "count": 1}},
    )

    assert "`MANAGE`, `UPDATE`, and `DELETE` require one validated target record" in prompt
    assert "If the target is unclear, prefer clarification" in prompt
    assert "If confidence is not high enough for a safe executable action, prefer clarification" in prompt


def test_build_reasoning_prompt_includes_minimal_noisy_input_examples():
    prompt = IntentReasoner.build_reasoning_prompt(
        metadata='{"tables": []}',
        language_preference="eng",
        reasoning_context={},
    )

    assert 'User: "delete that one"' in prompt
    assert 'User: "can u pull the contact i just added"' in prompt
    assert '"requires_clarification": true' in prompt
    assert '"intent": "MANAGE"' in prompt


def test_build_reasoning_prompt_guides_query_result_and_query_clarification_behavior():
    prompt = IntentReasoner.build_reasoning_prompt(
        metadata='{"tables": []}',
        language_preference="eng",
        reasoning_context={},
    )

    assert 'User: "open the last contact from the list"' in prompt
    assert '"kind": "query_result"' in prompt
    assert "If the wording sounds like a search but the filters are incomplete or weak, prefer clarification" in prompt


# Safe Executable Outcomes


def test_validate_reasoning_output_resolves_last_created_reference():
    result = _validated(
        {
            "intent": "MANAGE",
            "object_type": "lead",
            "context_reference": {"kind": "last_created"},
            "confidence": 0.92,
        },
        "show the one I just created",
        _context(
            last_created={"object_type": "lead", "record_id": "LEAD-R1"},
            last_record={"object_type": "lead", "record_id": "LEAD-R1"},
        ),
    )

    _assert_executable_result(result, intent="MANAGE", object_type="lead", record_id="LEAD-R1")
    assert result["reasoning"]["resolved_reference"]["record_id"] == "LEAD-R1"


def test_validate_reasoning_output_uses_last_query_result_for_negative_index():
    result = _validated(
        {
            "intent": "MANAGE",
            "object_type": "contact",
            "context_reference": {"kind": "query_result", "index": -1},
            "confidence": 0.83,
        },
        "open the last one",
        _context(
            query_results={
                "object_type": "contact",
                "results": [
                    {"record_id": "CONTACT-R7A", "label": "Ada Kim"},
                    {"record_id": "CONTACT-R7B", "label": "Ben Park"},
                ],
                "count": 2,
            }
        ),
    )

    _assert_executable_result(result, intent="MANAGE", record_id="CONTACT-R7B")


def test_validate_reasoning_output_normalizes_from_the_list_reference_to_query_result():
    result = _validated(
        {
            "intent": "MANAGE",
            "action": "manage",
            "object_type": "contact",
            "context_reference": {"kind": "from the list", "index": -1},
            "confidence": 0.84,
        },
        "open the last contact from the list",
        _context(
            query_results={
                "object_type": "contact",
                "results": [
                    {"record_id": "CONTACT-L1", "label": "Ada Kim"},
                    {"record_id": "CONTACT-L2", "label": "Ben Park"},
                ],
                "count": 2,
            }
        ),
    )

    _assert_executable_result(result, intent="MANAGE", object_type="contact", record_id="CONTACT-L2")


def test_validate_reasoning_output_normalizes_update_field_keys():
    result = _validated(
        {
            "intent": "UPDATE",
            "object_type": "lead",
            "resolved_reference": {"object_type": "lead", "record_id": "LEAD-R6"},
            "fields_to_update": {"First Name": "Ada", "lastname": "Kim", "phone": "010-1234-5678"},
            "confidence": 0.97,
        },
        "update that one",
        _context(last_record={"object_type": "lead", "record_id": "LEAD-R6"}),
    )

    assert result["intent"] == "UPDATE"
    assert result["data"] == {"first_name": "Ada", "last_name": "Kim", "phone": "010-1234-5678"}


def test_validate_reasoning_output_allows_safe_execution_at_threshold():
    result = _validated(
        {
            "intent": "MANAGE",
            "action": "manage",
            "object_type": "lead",
            "resolved_reference": {"object_type": "lead", "record_id": "LEAD-C1"},
            "confidence": 0.6,
        },
        "open that lead",
        _context(last_record={"object_type": "lead", "record_id": "LEAD-C1"}),
    )

    _assert_executable_result(
        result,
        intent="MANAGE",
        record_id="LEAD-C1",
        confidence_band="medium",
    )


def test_validate_reasoning_output_keeps_high_confidence_safe_execution_working():
    result = _validated(
        {
            "intent": "UPDATE",
            "action": "update",
            "object_type": "contact",
            "resolved_reference": {"object_type": "contact", "record_id": "CONTACT-C2"},
            "fields_to_update": {"phone num": "01012345678"},
            "confidence": 0.93,
        },
        "pls update the contact phone num to 01012345678",
        _context(last_record={"object_type": "contact", "record_id": "CONTACT-C2"}),
    )

    _assert_executable_result(
        result,
        intent="UPDATE",
        object_type="contact",
        record_id="CONTACT-C2",
        confidence_band="high",
    )
    assert result["data"] == {"phone": "01012345678"}


# Target Safety And Clarification Priority Regression Proof


def test_validate_reasoning_output_requires_specific_record_for_update():
    result = _validated(
        {
            "intent": "UPDATE",
            "object_type": "contact",
            "fields_to_update": {"status": "Qualified"},
            "confidence": 0.88,
        },
        "update that contact",
        _context(),
    )

    _assert_chat_clarification(
        result,
        "specific contact record",
        "name, ID, or a single clear selection",
    )
    assert result["object_type"] == "contact"


def test_validate_reasoning_output_preserves_field_intent_when_update_target_is_missing():
    result = _validated(
        {
            "intent": "UPDATE",
            "action": "update",
            "object_type": "contact",
            "fields_to_update": {"phone num": "01012345678"},
            "confidence": 0.89,
        },
        "update john phone num to 01012345678",
        _context(),
    )

    _assert_chat_clarification(
        result,
        "specific contact record",
        "change to phone",
    )


def test_validate_reasoning_output_explains_multi_selection_clarification():
    result = _validated(
        {
            "intent": "DELETE",
            "object_type": "contact",
            "confidence": 0.91,
        },
        "delete that selected contact",
        _context(
            selection={
                "object_type": "contact",
                "record_ids": ["CONTACT-R8A", "CONTACT-R8B"],
                "labels": ["Ada Kim", "Ben Park"],
                "count": 2,
            },
            safety={
                "has_multi_selection": True,
                "has_selection_conflict": False,
            },
        ),
    )

    _assert_chat_clarification(
        result,
        "multiple selected contact records",
        "select only one record first",
    )


def test_validate_reasoning_output_prioritizes_clarification_over_executable_shape():
    result = _validated(
        {
            "intent": "DELETE",
            "action": "delete",
            "object_type": "lead",
            "resolved_reference": {"object_type": "lead", "record_id": "LEAD-R11"},
            "requires_clarification": True,
            "clarification_question": "Please confirm which lead you meant.",
            "confidence": 0.98,
        },
        "delete that lead",
        _context(last_record={"object_type": "lead", "record_id": "LEAD-R11"}),
    )

    _assert_chat_clarification(result)
    assert result["text"] == "Please confirm which lead you meant."


def test_validate_reasoning_output_high_confidence_does_not_override_target_safety_failure():
    result = _validated(
        {
            "intent": "DELETE",
            "action": "delete",
            "object_type": "lead",
            "confidence": 0.97,
        },
        "delete that lead",
        _context(),
    )

    _assert_chat_clarification(result, "specific lead record")


# Contract Safety Failures Regression Proof


def test_validate_reasoning_output_refuses_conflicting_intent_and_action():
    result = _validated(
        {
            "intent": "UPDATE",
            "action": "delete",
            "object_type": "lead",
            "resolved_reference": {"object_type": "lead", "record_id": "LEAD-R9"},
            "confidence": 0.95,
        },
        "change that lead",
        _context(last_record={"object_type": "lead", "record_id": "LEAD-R9"}),
    )

    _assert_chat_clarification(result, "intent `UPDATE` but action `delete`")


def test_validate_reasoning_output_refuses_mixed_object_query():
    result = _validated(
        {
            "intent": "MANAGE",
            "object_type": "lead",
            "confidence": 0.91,
            "resolved_reference": {"object_type": "lead", "record_id": "LEAD-R4"},
        },
        "open the lead and contact",
        _context(last_record={"object_type": "lead", "record_id": "LEAD-R4"}),
    )

    _assert_chat_clarification(result, "multiple objects", "single object")


def test_validate_reasoning_output_refuses_resolved_reference_mismatch():
    result = _validated(
        {
            "intent": "UPDATE",
            "object_type": "contact",
            "resolved_reference": {"object_type": "lead", "record_id": "LEAD-R5"},
            "fields_to_update": {"Status": "Qualified"},
            "confidence": 0.94,
        },
        "update that contact",
        _context(last_record={"object_type": "lead", "record_id": "LEAD-R5"}),
    )

    _assert_chat_clarification(
        result,
        "found a lead record in context",
        "specific contact record",
    )


def test_validate_reasoning_output_requires_object_for_executable_intent():
    result = _validated(
        {
            "intent": "QUERY",
            "action": "query",
            "confidence": 0.88,
            "filters": {"status": "New"},
        },
        "show me those",
        _context(),
    )

    _assert_chat_clarification(result, "did not identify an object")


def test_validate_reasoning_output_clarifies_context_reference_without_object():
    result = _validated(
        {
            "intent": "MANAGE",
            "action": "manage",
            "context_reference": {"kind": "from before"},
            "confidence": 0.82,
        },
        "show something from before",
        _context(),
    )

    _assert_chat_clarification(
        result,
        "referring to an earlier record in context",
        "need the object and the exact record",
    )


def test_validate_reasoning_output_refuses_query_with_update_fields():
    result = _validated(
        {
            "intent": "QUERY",
            "action": "query",
            "object_type": "lead",
            "filters": {"status": "New"},
            "fields_to_update": {"status": "Qualified"},
            "confidence": 0.93,
        },
        "find leads and set status qualified",
        _context(),
    )

    _assert_chat_clarification(result, "mixed query filters with update fields")


def test_validate_reasoning_output_refuses_create_with_sql():
    result = _validated(
        {
            "intent": "CREATE",
            "action": "create",
            "object_type": "contact",
            "fields_to_update": {"last_name": "Kim", "status": "New"},
            "sql": "SELECT * FROM contacts",
            "confidence": 0.94,
        },
        "create contact Kim",
        _context(),
    )

    _assert_chat_clarification(result, "returned SQL for a create request")


def test_validate_reasoning_output_requires_fields_for_create():
    result = _validated(
        {
            "intent": "CREATE",
            "action": "create",
            "object_type": "lead",
            "confidence": 0.96,
        },
        "create lead",
        _context(),
    )

    _assert_chat_clarification(result, "did not produce any fields to create the lead")


def test_validate_reasoning_output_requires_fields_for_update():
    result = _validated(
        {
            "intent": "UPDATE",
            "action": "update",
            "object_type": "contact",
            "resolved_reference": {"object_type": "contact", "record_id": "CONTACT-R10"},
            "confidence": 0.97,
        },
        "update that contact",
        _context(last_record={"object_type": "contact", "record_id": "CONTACT-R10"}),
    )

    _assert_chat_clarification(result, "did not produce any fields to update on the contact")


def test_validate_reasoning_output_requires_query_detail_for_weak_noisy_search():
    result = _validated(
        {
            "intent": "QUERY",
            "action": "query",
            "object_type": "opportunity",
            "confidence": 0.83,
        },
        "need the opp from samsung next week",
        _context(),
    )

    _assert_chat_clarification(
        result,
        "opportunity search",
        "add one filter, date range, or a specific record reference",
    )


# Confidence Policy Regression Proof


def test_validate_reasoning_output_refuses_low_confidence_execution():
    result = _validated(
        {
            "intent": "DELETE",
            "object_type": "lead",
            "resolved_reference": {"object_type": "lead", "record_id": "LEAD-R3"},
            "confidence": 0.32,
        },
        "delete that lead",
        _context(last_record={"object_type": "lead", "record_id": "LEAD-R3"}),
    )

    _assert_chat_clarification(
        result,
        "only have low confidence",
        "restate the lead and the action in one sentence",
        confidence_band="low",
    )


def test_validate_reasoning_output_keeps_medium_confidence_ambiguous_request_in_clarification():
    result = _validated(
        {
            "intent": "DELETE",
            "action": "delete",
            "object_type": "lead",
            "context_reference": {"kind": "that one"},
            "confidence": 0.67,
        },
        "delete that one",
        _context(),
    )

    _assert_chat_clarification(
        result,
        "mean a recent lead",
        "exact lead record",
        confidence_band="medium",
    )


def test_validate_reasoning_output_low_confidence_noisy_execution_prompt_stays_blocked():
    result = _validated(
        {
            "intent": "UPDATE",
            "action": "update",
            "object_type": "contact",
            "resolved_reference": {"object_type": "contact", "record_id": "CONTACT-C3"},
            "fields_to_update": {"phone num": "01012345678"},
            "confidence": 0.41,
        },
        "pls update the last one",
        _context(last_record={"object_type": "contact", "record_id": "CONTACT-C3"}),
    )

    _assert_chat_clarification(result, "only have medium confidence", confidence_band="medium")


def test_validate_reasoning_output_keeps_chat_permissive():
    result = _validated(
        {
            "intent": "CHAT",
            "action": "chat",
            "text": "I can help with that. Tell me more.",
            "confidence": 0.22,
            "filters": {"status": "New"},
            "fields_to_update": {"status": "Qualified"},
        },
        "help",
        _context(),
    )

    _assert_chat_clarification(result, confidence_band="low")
    assert result["text"] == "I can help with that. Tell me more."
    assert result["reasoning"]["action"] == "chat"


# Noisy English Input Regression Proof


def test_validate_reasoning_output_handles_noisy_shorthand_last_opp_safely():
    result = _validated(
        {
            "intent": "MANAGE",
            "action": "manage",
            "context_reference": {"kind": "last_record"},
            "confidence": 0.84,
        },
        "show me the last opp i made",
        _context(last_record={"object_type": "opportunity", "record_id": "OPP-N1"}),
    )

    _assert_executable_result(result, intent="MANAGE", object_type="opportunity", record_id="OPP-N1")


def test_validate_reasoning_output_handles_noisy_just_added_contact_safely():
    result = _validated(
        {
            "intent": "MANAGE",
            "action": "manage",
            "context_reference": {"kind": "i just added"},
            "confidence": 0.86,
        },
        "can u pull the contact i just added",
        _context(last_created={"object_type": "contact", "record_id": "CONTACT-N2"}),
    )

    _assert_executable_result(result, intent="MANAGE", object_type="contact", record_id="CONTACT-N2")


def test_validate_reasoning_output_normalizes_phone_num_field_from_noisy_input():
    result = _validated(
        {
            "intent": "UPDATE",
            "action": "update",
            "object_type": "contact",
            "resolved_reference": {"object_type": "contact", "record_id": "CONTACT-N3"},
            "fields_to_update": {"phone num": "01012345678"},
            "confidence": 0.9,
        },
        "update john phone num to 01012345678",
        _context(last_record={"object_type": "contact", "record_id": "CONTACT-N3"}),
    )

    _assert_executable_result(result, intent="UPDATE", object_type="contact", record_id="CONTACT-N3")
    assert result["data"] == {"phone": "01012345678"}


def test_validate_reasoning_output_clarifies_noisy_update_without_validated_target():
    result = _validated(
        {
            "intent": "UPDATE",
            "action": "update",
            "object_type": "contact",
            "fields_to_update": {"phone num": "01012345678"},
            "confidence": 0.89,
        },
        "update john phone num to 01012345678",
        _context(),
    )

    _assert_chat_clarification(result, "specific contact record", "change to phone")


def test_validate_reasoning_output_clarifies_noisy_delete_that_one_without_context():
    result = _validated(
        {
            "intent": "DELETE",
            "action": "delete",
            "object_type": "lead",
            "context_reference": {"kind": "that one"},
            "confidence": 0.87,
        },
        "delete that one",
        _context(),
    )

    _assert_chat_clarification(result, "mean a recent lead", "exact lead record")


def test_validate_reasoning_output_clarifies_indirect_noisy_last_one_request_without_target():
    result = _validated(
        {
            "intent": "UPDATE",
            "action": "update",
            "context_reference": {"kind": "last one"},
            "confidence": 0.78,
        },
        "pls update the last one",
        _context(),
    )

    _assert_chat_clarification(
        result,
        "referring to an earlier record in context",
        "need the object and the exact record",
    )


def test_validate_reasoning_output_clarifies_mixed_object_noisy_request():
    result = _validated(
        {
            "intent": "QUERY",
            "action": "query",
            "object_type": "opportunity",
            "confidence": 0.83,
        },
        "need the opportunity from samsung next week and show the contact too",
        _context(),
    )

    _assert_chat_clarification(
        result,
        "fallback reasoning resolved opportunity",
        "do not act on the wrong record",
    )


def test_validate_reasoning_output_handles_indirect_last_record_phrase():
    result = _validated(
        {
            "intent": "MANAGE",
            "action": "manage",
            "context_reference": {"kind": "we were just looking at"},
            "confidence": 0.88,
        },
        "show me the contact we were just looking at",
        _context(last_record={"object_type": "contact", "record_id": "CONTACT-N4"}),
    )

    _assert_executable_result(result, intent="MANAGE", object_type="contact", record_id="CONTACT-N4")


def test_validate_reasoning_output_clarifies_from_the_list_without_safe_result():
    result = _validated(
        {
            "intent": "DELETE",
            "action": "delete",
            "object_type": "contact",
            "context_reference": {"kind": "from the list", "index": -1},
            "confidence": 0.88,
        },
        "delete the last contact from the list",
        _context(),
    )

    _assert_chat_clarification(
        result,
        "from the current contact list",
        "which result from the list",
    )


# Prompt-Guided Shape Stability Regression Proof


def test_validate_reasoning_output_supports_prompt_guided_last_created_contact_shape():
    result = _validated(
        {
            "intent": "MANAGE",
            "action": "manage",
            "object_type": "contact",
            "context_reference": {"kind": "last_created", "object_type": "contact"},
            "confidence": 0.86,
        },
        "can u pull the contact i just added",
        _context(last_created={"object_type": "contact", "record_id": "CONTACT-P3"}),
    )

    _assert_executable_result(result, intent="MANAGE", object_type="contact", record_id="CONTACT-P3")


# Fallback Integration Guard


@pytest.mark.asyncio
async def test_process_query_uses_validated_reasoner_output_for_fallback():
    conv_id = "reasoner-fallback-last-created"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_created(conv_id, "lead", "LEAD-R2")

    execute_intent = AsyncMock(side_effect=lambda _db, agent_output, _query, **_kwargs: agent_output)

    with patch.object(
        AiAgentService,
        "_call_multi_llm_ensemble",
        return_value={
            "intent": "MANAGE",
            "object_type": "lead",
            "context_reference": {"kind": "last_created"},
            "confidence": 0.91,
        },
    ), patch.object(AiAgentService, "_execute_intent", execute_intent):
        response = await AiAgentService.process_query(
            db=None,
            user_query="work with the one I just created",
            conversation_id=conv_id,
        )

    assert response["intent"] == "MANAGE"
    assert response["object_type"] == "lead"
    assert response["record_id"] == "LEAD-R2"
    execute_intent.assert_awaited_once()
