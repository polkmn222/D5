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


def test_home_send_message_ui_gates_demo_relay_availability_before_send():
    source = Path("development/web/message/frontend/templates/send_message.html").read_text(encoding="utf-8")

    assert 'id="demo-relay-status-banner"' in source
    assert 'id="demo-message-send-btn"' in source
    assert "fetch('/messaging/demo-availability')" in source
    assert "ensureDemoRelayAvailability()" in source
    assert "Demo message service unavailable. Contact the administrator." in source


def test_static_template_manager_defers_upload_until_save():
    source = Path("development/web/frontend/static/js/messaging.js").read_text(encoding="utf-8")

    assert "Image selected. It will be saved when you save the template." in source
    assert "await this.uploadPendingModalImage();" in source


def test_template_detail_image_changes_are_staged_until_save():
    source = Path("development/web/message/frontend/templates/message_templates/detail_view.html").read_text(encoding="utf-8")

    assert "Image selected. It will be saved when you click Save." in source
    assert "await persistTemplateDetailImageChanges(recordId);" in source
    assert "Image removal staged. Click Save to apply it." in source
