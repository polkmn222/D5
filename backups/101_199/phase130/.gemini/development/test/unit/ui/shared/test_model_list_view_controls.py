from pathlib import Path

from fastapi.testclient import TestClient
from starlette.requests import Request
from unittest.mock import patch

from db.database import Base, engine
from web.backend.app.main import app
from web.backend.app.core.templates import templates


APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
MODEL_LIST_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "models" / "list_view.html"
MODEL_DETAIL_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "models" / "detail_view.html"
LIST_VIEW_JS = APP_ROOT / "web" / "frontend" / "static" / "js" / "list_views.js"


def build_request(path: str = "/models") -> Request:
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


def test_model_list_template_contains_custom_list_view_controls():
    html = MODEL_LIST_TEMPLATE.read_text()
    assert "model-list-view-selector" in html
    assert "model-list-view-trigger" in html
    assert "model-list-view-menu" in html
    assert "Customize Model List View" in html
    assert "window.applyModelListView(this.value)" in html
    assert "window.toggleModelListViewPin()" in html
    assert "sf-list-view-icon--model" in html
    assert "d4_recent_models" in html


def test_model_detail_template_tracks_recently_viewed_records():
    html = MODEL_DETAIL_TEMPLATE.read_text()
    assert "rememberRecentlyViewedRecord" in html
    assert "d4_recent_models" in html


def test_list_view_assets_include_model_list_logic():
    js = LIST_VIEW_JS.read_text()
    assert "initializeModelListView" in js
    assert "applyModelListView" in js
    assert "toggleModelListViewPin" in js
    assert "objectApiPath: \"/models/views\"" in js


def test_model_list_template_renders_with_default_context():
    html = templates.get_template("models/list_view.html").render({
        "request": build_request(),
        "object_type": "Model",
        "plural_type": "models",
        "items": [],
        "columns": ["name", "brand", "description"],
    })
    assert "All Models" in html
    assert "Setup" in html


def test_model_list_template_shows_pagination_controls_when_present():
    html = templates.get_template("models/list_view.html").render({
        "request": build_request(),
        "object_type": "Model",
        "plural_type": "models",
        "items": [],
        "columns": ["name", "brand", "description"],
        "current_view": "model-all",
    })
    assert "Page 3 of 5" not in html
    assert "Previous" not in html
    assert "Next" not in html


def test_model_list_route_supports_saved_view_context():
    Base.metadata.create_all(bind=engine)
    with patch("web.backend.app.api.routers.vehicle_spec_router.ModelService.get_models", return_value=[]), patch(
        "web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.list_views",
        return_value=[
            {"id": "model-all", "label": "All Models", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "model-recent", "label": "Recently Viewed", "source": "recent", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "ev", "label": "EV Models", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "brand", "operator": "contains", "value": "EV"}]}, "editable": True, "isPinned": True},
        ],
    ):
        with TestClient(app) as client:
            response = client.get("/models?view=ev")
    assert response.status_code == 200
    assert "EV Models" in response.text


def test_model_list_view_api_routes_support_create_update_delete_and_pin():
    Base.metadata.create_all(bind=engine)
    view = {"id": "ev", "label": "EV Models", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": True, "isPinned": False}
    updated = {**view, "label": "Hybrid Models", "isPinned": True}
    with patch("web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.create_view", return_value=view), patch(
        "web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.update_view", return_value=updated
    ), patch(
        "web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.delete_view", return_value=None
    ), patch(
        "web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.set_pinned_view", return_value="ev"
    ):
        with TestClient(app) as client:
            assert client.post("/models/views", json={"label": "EV Models"}).status_code == 200
            assert client.put("/models/views/ev", json={"label": "Hybrid Models"}).status_code == 200
            assert client.post("/models/views/ev/pin", json={"pinned": True}).status_code == 200
            assert client.delete("/models/views/ev").status_code == 200
