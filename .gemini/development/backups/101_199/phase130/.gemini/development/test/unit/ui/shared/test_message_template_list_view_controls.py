from pathlib import Path

from fastapi.testclient import TestClient
from starlette.requests import Request
from unittest.mock import patch

from db.database import Base, engine
from web.backend.app.main import app
from web.backend.app.core.templates import templates


APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
TEMPLATE_LIST_TEMPLATE = APP_ROOT / "web" / "message" / "frontend" / "templates" / "message_templates" / "list_view.html"
TEMPLATE_DETAIL_TEMPLATE = APP_ROOT / "web" / "message" / "frontend" / "templates" / "message_templates" / "detail_view.html"
LIST_VIEW_JS = APP_ROOT / "web" / "frontend" / "static" / "js" / "list_views.js"


def build_request(path: str = "/message_templates/") -> Request:
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


def test_message_template_list_template_contains_custom_list_view_controls():
    html = TEMPLATE_LIST_TEMPLATE.read_text()
    assert "message-template-list-view-selector" in html
    assert "Customize Template List View" in html
    assert "window.applyMessageTemplateListView(this.value)" in html
    assert "window.toggleMessageTemplateListViewPin()" in html
    assert "sf-list-view-icon--template" in html
    assert "d4_recent_message_templates" in html


def test_message_template_detail_template_tracks_recently_viewed_records():
    html = TEMPLATE_DETAIL_TEMPLATE.read_text()
    assert "rememberRecentlyViewedRecord" in html
    assert "d4_recent_message_templates" in html


def test_list_view_assets_include_message_template_list_logic():
    js = LIST_VIEW_JS.read_text()
    assert "initializeMessageTemplateListView" in js
    assert "applyMessageTemplateListView" in js
    assert "toggleMessageTemplateListViewPin" in js
    assert "objectApiPath: \"/message_templates/views\"" in js


def test_message_template_list_template_renders_with_default_context():
    html = templates.get_template("message_templates/list_view.html").render({
        "request": build_request(),
        "object_type": "MessageTemplate",
        "plural_type": "message_templates",
        "items": [],
        "columns": ["name", "subject", "content", "type"],
    })
    assert "All Templates" in html
    assert "Setup" in html


def test_message_template_list_route_supports_saved_view_context():
    Base.metadata.create_all(bind=engine)
    with patch("web.message.backend.routers.message_template_router.MessageTemplateService.get_templates", return_value=[]), patch(
        "web.message.backend.routers.message_template_router.LeadListViewService.list_views",
        return_value=[
            {"id": "template-all", "label": "All Templates", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "template-recent", "label": "Recently Viewed", "source": "recent", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "sms", "label": "SMS Templates", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "type", "operator": "contains", "value": "SMS"}]}, "editable": True, "isPinned": True},
        ],
    ):
        with TestClient(app) as client:
            response = client.get("/message_templates?view=sms")
    assert response.status_code == 200
    assert "SMS Templates" in response.text


def test_message_template_list_view_api_routes_support_create_update_delete_and_pin():
    Base.metadata.create_all(bind=engine)
    view = {"id": "sms", "label": "SMS Templates", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": True, "isPinned": False}
    updated = {**view, "label": "MMS Templates", "isPinned": True}
    with patch("web.message.backend.routers.message_template_router.LeadListViewService.create_view", return_value=view), patch(
        "web.message.backend.routers.message_template_router.LeadListViewService.update_view", return_value=updated
    ), patch(
        "web.message.backend.routers.message_template_router.LeadListViewService.delete_view", return_value=None
    ), patch(
        "web.message.backend.routers.message_template_router.LeadListViewService.set_pinned_view", return_value="sms"
    ):
        with TestClient(app) as client:
            assert client.post("/message_templates/views", json={"label": "SMS Templates"}).status_code == 200
            assert client.put("/message_templates/views/sms", json={"label": "MMS Templates"}).status_code == 200
            assert client.post("/message_templates/views/sms/pin", json={"pinned": True}).status_code == 200
            assert client.delete("/message_templates/views/sms").status_code == 200
