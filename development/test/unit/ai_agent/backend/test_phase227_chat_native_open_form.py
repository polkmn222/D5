from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_incomplete_create_lead_returns_chat_native_open_form():
    response = await AiAgentService.process_query(
        db=None,
        user_query="create lead",
        conversation_id="phase227-lead-form",
    )

    assert response["intent"] == "OPEN_FORM"
    assert response["object_type"] == "lead"
    assert response["form"]["mode"] == "create"
    assert response["form"]["required_fields"] == ["last_name", "status"]
    assert any(field["name"] == "last_name" for field in response["form"]["fields"])


@pytest.mark.asyncio
async def test_partial_create_contact_prefills_chat_native_form():
    response = await AiAgentService.process_query(
        db=None,
        user_query="create contact first name Ada email ada@example.com",
        conversation_id="phase227-contact-form",
    )

    assert response["intent"] == "OPEN_FORM"
    field_values = {field["name"]: field.get("value") for field in response["form"]["fields"]}
    assert field_values["first_name"] == "Ada"
    assert field_values["email"] == "ada@example.com"
    assert field_values["last_name"] in ("", None)


@pytest.mark.asyncio
async def test_edit_opportunity_returns_prefilled_scalar_only_form():
    opportunity = SimpleNamespace(
        id="OPP227",
        name="Fleet Renewal",
        amount=120000,
        stage="Qualification",
        status="Open",
        probability=70,
        temperature="Warm",
        contact="CONTACT1",
        brand="BRAND1",
        model="MODEL1",
        product="PROD1",
        asset="ASSET1",
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.get_opportunity", return_value=opportunity):
        response = await AiAgentService.process_query(
            db=None,
            user_query="edit opportunity OPP227",
            conversation_id="phase227-opp-edit",
        )

    assert response["intent"] == "OPEN_FORM"
    fields = {field["name"] for field in response["form"]["fields"]}
    assert fields == {"name", "amount", "stage", "status", "probability", "temperature"}


@pytest.mark.asyncio
async def test_submit_chat_native_lead_create_returns_open_record():
    lead = SimpleNamespace(
        id="LEAD227",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="New",
        gender="Female",
        description="Priority lead",
    )

    with patch("web.backend.app.services.lead_service.LeadService.create_lead", return_value=lead):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="lead",
            mode="create",
            values={
                "first_name": "Ada",
                "last_name": "Kim",
                "email": "ada@example.com",
                "phone": "01012345678",
                "status": "New",
                "gender": "Female",
                "description": "Priority lead",
            },
            conversation_id="phase227-submit-create",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["object_type"] == "lead"
    assert response["record_id"] == "LEAD227"


@pytest.mark.asyncio
async def test_submit_chat_native_opportunity_edit_validation_error_returns_open_form():
    opportunity = SimpleNamespace(
        id="OPP227E",
        name="Fleet Renewal",
        amount=120000,
        stage="Qualification",
        status="Open",
        probability=70,
        temperature="Warm",
    )

    with patch("web.backend.app.services.opportunity_service.OpportunityService.get_opportunity", return_value=opportunity):
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="opportunity",
            mode="edit",
            record_id="OPP227E",
            values={
                "name": "Fleet Renewal",
                "amount": "120000",
                "stage": "Qualification",
                "status": "Open",
                "probability": "120",
                "temperature": "Warm",
            },
            conversation_id="phase227-submit-edit",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_FORM"
    assert response["form"]["field_errors"]["probability"] == "Probability must be between 0 and 100."


@pytest.mark.asyncio
async def test_submit_chat_native_contact_edit_uses_updated_record_without_extra_refetch():
    contact = SimpleNamespace(
        id="CONTACT232",
        first_name="Ada",
        last_name="Kim",
        email="ada@example.com",
        phone="01012345678",
        status="Qualified",
        website="https://example.com",
        tier="Gold",
        description="VIP contact",
    )

    with patch("web.backend.app.services.contact_service.ContactService.update_contact", return_value=contact) as update_contact, patch(
        "web.backend.app.services.contact_service.ContactService.get_contact"
    ) as get_contact:
        response = await AiAgentService.submit_chat_native_form(
            db=None,
            object_type="contact",
            mode="edit",
            record_id="CONTACT232",
            values={
                "first_name": "Ada",
                "last_name": "Kim",
                "email": "ada@example.com",
                "phone": "01012345678",
                "status": "Qualified",
            },
            conversation_id="phase232-contact-update",
            language_preference="eng",
        )

    assert response["intent"] == "OPEN_RECORD"
    assert response["record_id"] == "CONTACT232"
    update_contact.assert_called_once()
    get_contact.assert_not_called()


def test_ai_agent_frontend_has_schema_open_form_branch_and_submit_endpoint():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "if (data.intent === 'OPEN_FORM' && data.form?.fields) {" in source
    assert "appendAgentSchemaFormMessage(data.text || 'I opened the form for you.', data.form);" in source
    assert "fetch('/ai-agent/api/form-submit'" in source
    assert "function renderAgentInlineSchemaForm(form) {" in source
    assert "function submitAgentChatForm(event) {" in source


def test_ai_agent_frontend_uses_chat_native_form_card_not_workspace_for_schema_forms():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    branch_start = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields) {")
    branch_end = source.index("if (data.intent === 'OPEN_FORM' && data.form_url) {", branch_start)
    branch = source[branch_start:branch_end]

    assert "openAgentWorkspace" not in branch
    assert "appendAgentSchemaFormMessage" in branch


def test_ai_agent_frontend_scrolls_chat_native_form_into_view_on_initial_render():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "function scrollAgentSchemaFormIntoView(target) {" in source
    assert "scrollAgentSchemaFormIntoView(msgDiv);" in source
    assert "target.scrollIntoView({ behavior: 'smooth', block: 'start' });" in source


def test_ai_agent_frontend_scrolls_replaced_form_after_validation_refresh():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "const replacementCard = wrapper.firstElementChild;" in source
    assert "card.replaceWith(replacementCard);" in source
    assert "scrollAgentSchemaFormIntoView(replacementCard);" in source


def test_ai_agent_frontend_routes_phase_objects_selection_edit_through_chat_forms():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    edit_start = source.index("function triggerSelectionEdit() {")
    edit_end = source.index("function triggerSelectionDelete()", edit_start)
    edit_branch = source[edit_start:edit_end]

    assert "function shouldUseAgentChatForm(objectType) {" in source
    assert "return objectType === 'lead' || objectType === 'contact' || objectType === 'opportunity';" in source
    assert "if (shouldUseAgentChatForm(selection.object_type)) {" in edit_branch
    assert "sendAiMessageWithDisplay(`Edit ${label}`, `Manage ${selection.object_type} ${selection.ids[0]} edit`);" in edit_branch


def test_ai_agent_frontend_renders_open_record_feedback_before_workspace_fetch():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")
    start = source.index("if (data.intent === 'OPEN_RECORD') {")
    end = source.index("if (data.intent === 'OPEN_FORM' && data.form?.fields && card) {", start)
    branch = source[start:end]

    assert "appendChatMessage('agent', data.text" in branch
    assert "requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle));" in branch
    assert branch.index("appendChatMessage('agent', data.text") < branch.index("requestAnimationFrame(() => openAgentWorkspace(targetUrl, workspaceTitle));")
