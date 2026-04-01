from pathlib import Path

from fastapi.testclient import TestClient

from web.backend.app.main import app


client = TestClient(app)


def test_create_template_route_rejects_mms_without_image():
    response = client.post(
        "/message_templates/",
        data={
            "name": "No Image MMS",
            "record_type": "MMS",
            "subject": "Subject",
            "content": "Content",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "MMS+templates+require+a+JPG+image+under+500KB" in response.headers["location"]


def test_ai_agent_delete_buttons_use_safe_click_handling():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert 'type="button" class="${actionClass}"' in source
    assert 'type="button" class="${btnClass}"' in source
    assert "event.stopPropagation();" in source
    assert "return false;" in source


def test_ai_agent_inline_save_opens_workspace_after_redirect():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "Open the saved record directly instead of relying on a second chat turn." in source
    assert "openAgentWorkspace(finalUrl.pathname, workspaceTitle);" in source


def test_ai_agent_inline_save_reports_non_redirect_failures_in_chat():
    source = Path("development/ai_agent/ui/frontend/static/js/ai_agent.js").read_text(encoding="utf-8")

    assert "Save did not complete. Review the highlighted form and try again." in source


def test_home_send_message_template_modal_defers_upload_until_save():
    source = Path("development/web/message/frontend/templates/send_message.html").read_text(encoding="utf-8")

    assert "Template image selected. It will be saved when you save the template." in source
    assert "await uploadPendingTemplateModalImage();" in source
    assert '<div class="sf-modal-header"' in source
    assert 'MessageTemplate Information' in source
    assert 'id="send-message-template-modal-grid"' in source
    assert 'id="modal-form-image-empty"' in source
    assert 'Clear Selection' in source


def test_send_message_template_picker_supports_search_without_preview_card():
    source = Path("development/web/message/frontend/templates/send_message.html").read_text(encoding="utf-8")

    assert 'id="template-search"' in source
    assert 'id="template-search-results"' in source
    assert 'id="template-select"' in source
    assert "function captureTemplateSelectOptions() {" in source
    assert "function renderTemplateSearchResults(term = '', preserveValue = '') {" in source
    assert "function filterTemplateSelect(term) {" in source
    assert "function selectTemplateFromSearch(templateId) {" in source
    assert "renderTemplateSelectOptions('');" in source
    assert 'id="template-preview-card"' not in source
    assert 'id="preview-template-btn"' not in source


def test_send_message_saved_recipients_use_collapsible_table():
    source = Path("development/web/message/frontend/templates/send_message.html").read_text(encoding="utf-8")

    assert 'id="staged-message-panel"' in source
    assert 'id="staged-message-table-body"' in source
    assert "function renderStagedRecipientsTable() {" in source
    assert "Saved Recipients (" in source
    assert 'id="staged-message-summary"' not in source


def test_home_send_message_ui_gates_demo_relay_availability_before_send():
    source = Path("development/web/message/frontend/templates/send_message.html").read_text(encoding="utf-8")

    assert 'id="demo-relay-status-banner"' in source
    assert 'id="demo-message-send-btn"' in source
    assert "fetch('/messaging/demo-availability')" in source
    assert "ensureDemoRelayAvailability()" in source
    assert "Contact the administrator" in source
    assert "Contact Administrator" in source


def test_send_message_ui_initializes_ai_agent_guidance_banner():
    source = Path("development/web/message/frontend/templates/send_message.html").read_text(encoding="utf-8")

    assert "function initializeAiAgentGuidance() {" in source
    assert "sessionStorage.getItem('aiAgentMessageGuidance')" in source
    assert "AI Agent opened Send Message for you." in source
    assert "document.getElementById('recipient-search')?.focus();" in source
    assert "initializeAiAgentGuidance();" in source


def test_send_message_router_exposes_ai_agent_compose_data_endpoint():
    source = Path("development/web/message/backend/router.py").read_text(encoding="utf-8")

    assert '@router.get("/ai-agent-compose-data")' in source
    assert '"default_recipients": _load_default_recipient_rows(db)' in source
    assert '"templates": _load_message_template_rows(db)' in source
    assert '@router.get("/recommendations")' in source


def test_static_template_manager_defers_upload_until_save():
    source = Path("development/web/frontend/static/js/messaging.js").read_text(encoding="utf-8")

    assert "Image selected. It will be saved when you save the template." in source
    assert "await this.uploadPendingModalImage();" in source


def test_template_detail_image_changes_are_staged_until_save():
    source = Path("development/web/message/frontend/templates/message_templates/detail_view.html").read_text(encoding="utf-8")

    assert "Image selected. It will be saved when you click Save." in source
    assert "await persistTemplateDetailImageChanges(recordId);" in source
    assert 'id="template-detail-image-edit-panel"' in source
    assert "Image removal staged. Click Save to apply it." in source
    assert 'id="template-detail-image-edit-preview-wrap"' in source
    assert 'id="template-detail-image-edit-preview"' in source
    assert "const editPreviewWrap = document.getElementById('template-detail-image-edit-preview-wrap');" in source
    assert "if (editPreviewWrap) editPreviewWrap.style.display = 'block';" in source
    assert 'class="template-detail-image-actions"' in source
    assert '<input type="text" id="input-{{ field }}" class="sf-inline-input" value="{{ value | format_value }}" style="flex-grow: 1;">' not in source
    assert 'onclick="removeTemplateImage(\'{{ record_id }}\')">Clear Image</button>' in source


def test_send_message_action_buttons_use_save_recipients_and_clear_all():
    source = Path("development/web/message/frontend/templates/send_message.html").read_text(encoding="utf-8")

    assert "Save Recipients" in source
    assert "onclick=\"saveStagedMessages()\"" in source
    assert "onclick=\"clearAll()\"" in source
    assert 'id="staged-message-panel"' in source


def test_send_message_save_recipients_requires_selection_and_template_or_content():
    source = Path("development/web/message/frontend/templates/send_message.html").read_text(encoding="utf-8")

    assert "function hasMessageSource(messageConfig) {" in source
    assert "function validateRecipientSaveRequirements(selectedCount, messageConfig) {" in source
    assert "Select at least one recipient before saving recipients." in source
    assert "Select a template or enter message content before saving recipients." in source


def test_message_detail_view_renders_saved_message_image_when_present():
    source = Path("development/web/message/frontend/templates/messages/detail_view.html").read_text(encoding="utf-8")

    assert "{% if details.get('Image') %}" in source
    assert 'alt="Message image"' in source


def test_message_router_prefers_saved_message_type_subject_and_image():
    source = Path("development/web/message/backend/routers/message_router.py").read_text(encoding="utf-8")

    assert 'msg_type = getattr(m, "record_type", None)' in source
    assert '"Type": getattr(message, "record_type", None)' in source
    assert '"Subject": getattr(message, "subject", None) or ""' in source
    assert '"Image": getattr(message, "image_url", None) or ""' in source


def test_send_message_bulk_delete_uses_inline_template_delete_flow():
    source = Path("development/web/message/frontend/templates/send_message.html").read_text(encoding="utf-8")

    assert "function confirmTemplateBulkDelete() {" in source
    assert "object_type: 'MessageTemplate'" in source
    assert "closeBulkDeleteTemplatesModal();" in source
    assert "Deleted ${ids.length} templates." in source


def test_messages_list_view_restores_bulk_delete_button_for_message_object():
    source = Path("development/web/message/frontend/templates/messages/list_view.html").read_text(encoding="utf-8")
    bulk_source = Path("development/web/backend/app/api/routers/bulk_router.py").read_text(encoding="utf-8")

    assert "confirmBulkDelete('Message')" in source
    assert '"Message": MessageSend' in bulk_source
