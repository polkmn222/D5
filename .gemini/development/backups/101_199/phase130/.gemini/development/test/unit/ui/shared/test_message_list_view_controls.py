from pathlib import Path

from fastapi.testclient import TestClient
from starlette.requests import Request
from unittest.mock import patch

from db.database import Base, engine
from web.backend.app.main import app
from web.backend.app.core.templates import templates


APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
MESSAGE_LIST_TEMPLATE = APP_ROOT / "web" / "message" / "frontend" / "templates" / "messages" / "list_view.html"
MESSAGE_DETAIL_TEMPLATE = APP_ROOT / "web" / "message" / "frontend" / "templates" / "messages" / "detail_view.html"
LIST_VIEW_JS = APP_ROOT / "web" / "frontend" / "static" / "js" / "list_views.js"


def build_request(path: str = "/messages/") -> Request:
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


def test_message_list_template_contains_custom_list_view_controls():
    html = MESSAGE_LIST_TEMPLATE.read_text()
    assert "message-list-view-selector" in html
    assert "Customize Message List View" in html
    assert "window.applyMessageListView(this.value)" in html
    assert "window.toggleMessageListViewPin()" in html
    assert "sf-list-view-icon--message" in html
    assert "d4_recent_messages" in html
    assert "Setup" in html
    assert ">New<" not in html
    assert "Actions" in html
    assert ">View<" in html


def test_message_detail_template_tracks_recently_viewed_records():
    html = MESSAGE_DETAIL_TEMPLATE.read_text()
    assert "rememberRecentlyViewedRecord" in html
    assert "d4_recent_messages" in html


def test_list_view_assets_include_message_list_logic():
    js = LIST_VIEW_JS.read_text()
    assert "initializeMessageListView" in js
    assert "applyMessageListView" in js
    assert "toggleMessageListViewPin" in js
    assert "objectApiPath: \"/messages/views\"" in js


def test_message_list_template_renders_with_default_context():
    html = templates.get_template("messages/list_view.html").render({
        "request": build_request(),
        "object_type": "Message",
        "plural_type": "messages",
        "items": [],
        "columns": ["name", "direction", "status", "created_at"],
    })
    assert "All Messages" in html
    assert "Setup" in html


def test_message_list_template_shows_pagination_controls_when_present():
    html = templates.get_template("messages/list_view.html").render({
        "request": build_request(),
        "object_type": "Message",
        "plural_type": "messages",
        "items": [],
        "columns": ["name", "direction", "status", "created_at"],
        "current_view": "message-all",
    })

    assert "Page 2 of 3" not in html
    assert "Previous" not in html
    assert "Next" not in html


def test_message_list_route_supports_saved_view_context():
    Base.metadata.create_all(bind=engine)
    with patch("web.message.backend.routers.message_router.MessageService.get_messages", return_value=[]), patch(
        "web.message.backend.routers.message_router.LeadListViewService.list_views",
        return_value=[
            {"id": "message-all", "label": "All Messages", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "message-recent", "label": "Recently Viewed", "source": "recent", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "sent", "label": "Sent Queue", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "status", "operator": "contains", "value": "Sent"}]}, "editable": True, "isPinned": True},
        ],
    ):
        with TestClient(app) as client:
            response = client.get("/messages?view=sent")
    assert response.status_code == 200
    assert "Sent Queue" in response.text


def test_message_list_view_api_routes_support_create_update_delete_and_pin():
    Base.metadata.create_all(bind=engine)
    view = {"id": "sent", "label": "Sent Queue", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": True, "isPinned": False}
    updated = {**view, "label": "Outbound Queue", "isPinned": True}
    with patch("web.message.backend.routers.message_router.LeadListViewService.create_view", return_value=view), patch(
        "web.message.backend.routers.message_router.LeadListViewService.update_view", return_value=updated
    ), patch(
        "web.message.backend.routers.message_router.LeadListViewService.delete_view", return_value=None
    ), patch(
        "web.message.backend.routers.message_router.LeadListViewService.set_pinned_view", return_value="sent"
    ):
        with TestClient(app) as client:
            assert client.post("/messages/views", json={"label": "Sent Queue"}).status_code == 200
            assert client.put("/messages/views/sent", json={"label": "Outbound Queue"}).status_code == 200
            assert client.post("/messages/views/sent/pin", json={"pinned": True}).status_code == 200
            assert client.delete("/messages/views/sent").status_code == 200
