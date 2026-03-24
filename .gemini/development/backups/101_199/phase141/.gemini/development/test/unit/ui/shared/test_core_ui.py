from fastapi.testclient import TestClient
from pathlib import Path
from starlette.requests import Request
from unittest.mock import patch
from web.backend.app.main import app
from db.database import engine, Base
from web.backend.app.core.templates import templates

def test_dashboard_route():
    # Ensure tables are created for the test context
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        # Check for presence of navigation or specific dashboard elements
        assert "Home" in response.text or "Dashboard" in response.text


def build_request(path: str = "/") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "app": app,
        "router": app.router,
    }
    return Request(scope)

def test_static_css_load():
    # Note: style.css might have been renamed or moved in recent phases. 
    # Let's check for base.css which is usually present.
    with TestClient(app) as client:
        response = client.get("/static/css/base.css")
        if response.status_code != 200:
            # Fallback to style.css if base.css is missing
            response = client.get("/static/css/style.css")
        
        assert response.status_code == 200


def test_templates_register_temperature_label_filter():
    assert "temperature_label" in templates.env.filters


def test_base_template_includes_ajax_modal_submit_helpers():
    base_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/base.html").read_text()

    assert "function runJsonAction" in base_template
    assert "function enhanceModalForms" in base_template
    assert "enhanceModalForms(content);" in base_template
    assert "function showGlobalLoading" in base_template
    assert "function shouldSkipGlobalLoading" in base_template
    assert "function resetGlobalLoadingState" in base_template
    assert "sf-global-loading" in base_template


def test_shared_modal_templates_include_save_and_new_submit_mode():
    modal_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/sf_form_modal.html").read_text()
    nested_modal_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/templates/sf_form_modal.html").read_text()
    lead_modal_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/leads/create_edit_modal.html").read_text()

    assert 'data-submit-mode="save-new"' in modal_template
    assert 'data-submit-mode="save-new"' in nested_modal_template
    assert 'data-submit-mode="save-new"' in lead_modal_template


def test_dashboard_ai_recommendation_endpoint_handles_service_failures_gracefully():
    Base.metadata.create_all(bind=engine)
    with patch("ai_agent.backend.recommendations.AIRecommendationService.get_sendable_recommendations", side_effect=RuntimeError("boom")):
        with TestClient(app) as client:
            response = client.get("/api/recommendations")

    assert response.status_code == 200
    assert "Unable to load recommendations" in response.text


def test_message_template_routes_surface_errors_without_crashing_server():
    Base.metadata.create_all(bind=engine)
    with patch("web.message.backend.routers.message_template_router.MessageTemplateService.get_templates", side_effect=RuntimeError("template list failed")):
        with TestClient(app) as client:
            response = client.get("/message_templates/", headers={"referer": "/message_templates"})

    assert response.status_code in {200, 303}


def test_detail_templates_use_object_icons_and_hide_activity_tab():
    detail_templates = [
        ("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/leads/detail_view.html", "detail-icon--lead"),
        ("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/contacts/detail_view.html", "detail-icon--contact"),
        ("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/opportunities/detail_view.html", "detail-icon--opportunity"),
        ("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/products/detail_view.html", "detail-icon--product"),
        ("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/assets/detail_view.html", "detail-icon--asset"),
        ("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/brands/detail_view.html", "detail-icon--brand"),
        ("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/models/detail_view.html", "detail-icon--model"),
        ("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/message/frontend/templates/messages/detail_view.html", "detail-icon--message"),
        ("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/message/frontend/templates/message_templates/detail_view.html", "detail-icon--template"),
    ]

    for path, icon_class in detail_templates:
        template = Path(path).read_text()
        assert icon_class in template
        assert "tab-activity" not in template
        assert ">Activity<" not in template


def test_detail_templates_render_without_jinja_syntax_errors():
    detail_templates = [
        "brands/detail_view.html",
        "models/detail_view.html",
        "products/detail_view.html",
        "assets/detail_view.html",
    ]

    context = {
        "request": build_request(),
        "record_name": "Sample",
        "object_type": "Sample",
        "plural_type": "samples",
        "record_id": "001",
        "details": {"Name": "Sample"},
        "created_at": None,
        "updated_at": None,
        "related_lists": [],
        "path": [],
        "is_followed": False,
    }

    for template_name in detail_templates:
        html = templates.get_template(template_name).render(context)
        assert "Sample" in html


def test_lead_detail_template_no_longer_shows_follow_button():
    template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/leads/detail_view.html").read_text()
    assert "follow-btn" not in template
    assert "Followed" not in template


def test_list_view_styles_include_hover_affordance_for_view_picker():
    css = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/static/css/list_views.css").read_text()
    assert ".sf-list-view-hero-row:hover .sf-list-view-title-wrap" in css
    assert "cursor: pointer;" in css
    assert ".sf-list-view-trigger" in css
    assert ".sf-list-view-selector-menu" in css
    assert "min-width: 28rem;" in css
    assert "border: 0;" in css
    assert "max-height: min(78vh, 42rem);" in css
    assert ".sf-list-view-shell" in css and "overflow: visible;" in css
    assert ".sf-list-view-more-loader" in css


def test_detail_templates_keep_inline_edit_hooks_for_supported_objects():
    detail_templates = [
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/leads/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/contacts/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/opportunities/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/products/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/assets/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/brands/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/models/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/message/frontend/templates/message_templates/detail_view.html",
    ]

    for path in detail_templates:
        template = Path(path).read_text()
        assert "toggleInlineEdit(" in template
        assert 'id="edit-' in template


def test_detail_templates_include_required_system_metadata_fields():
    detail_templates = [
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/leads/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/contacts/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/opportunities/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/products/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/assets/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/brands/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/models/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/message/frontend/templates/messages/detail_view.html",
        "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/message/frontend/templates/message_templates/detail_view.html",
    ]

    partial = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/shared/detail_system_info.html").read_text()
    for label in ["Created Date", "Last Modified Date", "Created By", "Last Modified By"]:
        assert label in partial
    assert "field-grid sf-detail-meta-grid" in partial
    assert "sf-field-item--readonly-meta" in partial
    assert "sf-pencil-icon" not in partial

    for path in detail_templates:
        template = Path(path).read_text()
        assert '{% include "shared/detail_system_info.html" %}' in template


def test_message_detail_template_no_longer_contains_broken_follow_markup():
    template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/message/frontend/templates/messages/detail_view.html").read_text()
    assert "toggleFollow('{{plural_type}}'" not in template
    assert "Follow\n        </button>" not in template
    assert "openModal('/{{ plural_type }}/new?id={{ record_id }}')" not in template


def test_message_detail_template_is_read_only_and_uses_content_section():
    template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/message/frontend/templates/messages/detail_view.html").read_text()
    assert "toggleInlineEdit(" not in template
    assert 'id="edit-' not in template
    assert "<div class=\"sf-field-label\">Content</div>" in template
    assert "Description" not in template


def test_base_template_resets_loading_state_for_browser_navigation_restore():
    base_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/base.html").read_text()
    assert "window.addEventListener('pageshow'" in base_template
    assert "window.addEventListener('popstate'" in base_template
    assert "document.addEventListener('visibilitychange'" in base_template


def test_base_template_delegates_pencil_clicks_to_inline_edit_container():
    base_template = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/base.html").read_text()
    assert "const pencilIcon = event.target.closest('.sf-pencil-icon');" in base_template
    assert "editableField.click();" in base_template


def test_ui_standards_document_cross_object_consistency_rules():
    standards = Path("/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/docs/ui_standards.md").read_text()
    assert "Cross-Object UI Consistency" in standards
    assert "currency" in standards.lower()
    assert "lookup fields" in standards.lower()
