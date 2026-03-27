from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ai_agent.llm.backend.conversation_context import ConversationContextStore
from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_show_recent_leads_returns_query_and_remembers_ranked_results():
    conv_id = "phase230-recent-leads"
    ConversationContextStore.clear(conv_id)
    expected = {
        "results": [
            {"id": "LEAD230A", "display_name": "Ada Kim"},
            {"id": "LEAD230B", "display_name": "Ben Park"},
        ],
        "sql": "SELECT * FROM leads",
        "pagination": {"page": 1, "per_page": 30, "total": 2, "total_pages": 1, "object_type": "lead"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble"
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="show recent leads",
            conversation_id=conv_id,
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "lead"
    assert llm_call.await_count == 0
    assert ConversationContextStore.get_query_results(conv_id) == {
        "object_type": "lead",
        "results": [
            {"record_id": "LEAD230A", "label": "Ada Kim"},
            {"record_id": "LEAD230B", "label": "Ben Park"},
        ],
    }


@pytest.mark.asyncio
async def test_show_latest_contact_returns_recent_query_without_llm():
    conv_id = "phase230-latest-contact"
    ConversationContextStore.clear(conv_id)
    expected = {
        "results": [{"id": "CONTACT230Q", "display_name": "Ada Kim"}],
        "sql": "SELECT * FROM contacts",
        "pagination": {"page": 1, "per_page": 30, "total": 1, "total_pages": 1, "object_type": "contact"},
    }

    with patch.object(AiAgentService, "_execute_paginated_query", return_value=expected), patch.object(
        AiAgentService, "_call_multi_llm_ensemble"
    ) as llm_call:
        response = await AiAgentService.process_query(
            db=None,
            user_query="show latest contact",
            conversation_id=conv_id,
        )

    assert response["intent"] == "QUERY"
    assert response["object_type"] == "contact"
    assert response["data"]["query_mode"] == "recent"
    assert llm_call.await_count == 0


@pytest.mark.asyncio
async def test_open_first_one_uses_most_recent_ranked_list_result():
    conv_id = "phase230-open-first"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_query_results(
        conv_id,
        "lead",
        [
            {"id": "LEAD230OPEN1", "display_name": "Ada Kim"},
            {"id": "LEAD230OPEN2", "display_name": "Ben Park"},
        ],
    )
    record = SimpleNamespace(id="LEAD230OPEN1", first_name="Ada", last_name="Kim", status="New")

    with patch.object(AiAgentService, "_get_phase1_record", return_value=record), patch.object(
        AiAgentService,
        "_build_phase1_open_record_response",
        return_value={"intent": "OPEN_RECORD", "object_type": "lead", "record_id": "LEAD230OPEN1"},
    ) as build_open:
        response = await AiAgentService.process_query(
            db=None,
            user_query="open the first one",
            conversation_id=conv_id,
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["record_id"] == "LEAD230OPEN1"
    build_open.assert_called_once()


@pytest.mark.asyncio
async def test_edit_second_one_returns_edit_form_from_recent_contact_list():
    conv_id = "phase230-edit-second"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_query_results(
        conv_id,
        "contact",
        [
            {"id": "CONTACT230A", "display_name": "Ada Kim"},
            {"id": "CONTACT230B", "display_name": "Ben Park"},
        ],
    )
    record = SimpleNamespace(id="CONTACT230B", first_name="Ben", last_name="Park", status="New")

    with patch.object(AiAgentService, "_get_phase1_record", return_value=record), patch.object(
        AiAgentService,
        "_build_phase1_edit_form_response",
        return_value={"intent": "OPEN_FORM", "object_type": "contact", "record_id": "CONTACT230B"},
    ) as build_form:
        response = await AiAgentService.process_query(
            db=None,
            user_query="edit the second one",
            conversation_id=conv_id,
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["record_id"] == "CONTACT230B"
    build_form.assert_called_once()


def test_ranked_follow_up_without_recent_list_returns_clarification():
    conv_id = "phase230-no-list"
    ConversationContextStore.clear(conv_id)

    result = AiAgentService._resolve_contextual_query_reference("open the first one", conv_id)

    assert result is not None
    assert result["intent"] == "CHAT"
    assert "recent record list first" in result["text"]


def test_ranked_follow_up_does_not_cross_objects():
    conv_id = "phase230-cross-object"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_query_results(
        conv_id,
        "lead",
        [{"id": "LEAD230X", "display_name": "Ada Kim"}],
    )

    result = AiAgentService._resolve_contextual_query_reference("open the first contact", conv_id)

    assert result is not None
    assert result["intent"] == "CHAT"
    assert "shows leads, not contacts" in result["text"]


def test_reasoning_context_includes_recent_query_results():
    conv_id = "phase230-reasoning-query-context"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_query_results(
        conv_id,
        "contact",
        [
            {"id": "CONTACT230CTX1", "display_name": "Ada Kim"},
            {"id": "CONTACT230CTX2", "display_name": "Ben Park"},
        ],
    )

    result = ConversationContextStore.build_reasoning_context(conv_id)

    assert result["query_results"]["object_type"] == "contact"
    assert result["query_results"]["count"] == 2
    assert result["query_results"]["results"][0]["record_id"] == "CONTACT230CTX1"


def test_reasoning_context_marks_multi_selection():
    conv_id = "phase230-reasoning-multi-selection"
    ConversationContextStore.clear(conv_id)
    ConversationContextStore.remember_selection(
        conv_id,
        {"object_type": "contact", "ids": ["CONTACT230S1", "CONTACT230S2"], "labels": ["Ada Kim", "Ben Park"]},
    )

    result = ConversationContextStore.build_reasoning_context(conv_id)

    assert result["safety"]["has_multi_selection"] is True
