from pathlib import Path

from fastapi.testclient import TestClient
from starlette.requests import Request
from unittest.mock import patch

from db.database import Base, engine
from web.backend.app.main import app
from web.backend.app.core.templates import templates


APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
BRAND_LIST_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "brands" / "list_view.html"
BRAND_DETAIL_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "brands" / "detail_view.html"
LIST_VIEW_JS = APP_ROOT / "web" / "frontend" / "static" / "js" / "list_views.js"


def build_request(path: str = "/vehicle_specifications") -> Request:
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


def test_brand_list_template_contains_custom_list_view_controls():
    html = BRAND_LIST_TEMPLATE.read_text()
    assert "brand-list-view-selector" in html
    assert "Customize Brand List View" in html
    assert "window.applyBrandListView(this.value)" in html
    assert "window.toggleBrandListViewPin()" in html
    assert "sf-list-view-icon--brand" in html
    assert "d4_recent_brands" in html


def test_brand_detail_template_tracks_recently_viewed_records():
    html = BRAND_DETAIL_TEMPLATE.read_text()
    assert "rememberRecentlyViewedRecord" in html
    assert "d4_recent_brands" in html


def test_list_view_assets_include_brand_list_logic():
    js = LIST_VIEW_JS.read_text()
    assert "initializeBrandListView" in js
    assert "applyBrandListView" in js
    assert "toggleBrandListViewPin" in js
    assert "objectApiPath: \"/vehicle_specifications/views\"" in js


def test_brand_list_template_renders_with_default_context():
    html = templates.get_template("brands/list_view.html").render({
        "request": build_request(),
        "object_type": "Brand",
        "plural_type": "vehicle_specifications",
        "items": [],
        "columns": ["name", "type", "description"],
    })
    assert "All Brands" in html
    assert "Setup" in html


def test_brand_list_route_supports_saved_view_context():
    Base.metadata.create_all(bind=engine)
    with patch("web.backend.app.api.routers.vehicle_spec_router.VehicleSpecificationService.get_vehicle_specs", return_value=[]), patch(
        "web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.list_views",
        return_value=[
            {"id": "brand-all", "label": "All Brands", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "brand-recent", "label": "Recently Viewed", "source": "recent", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "legacy", "label": "Legacy Brands", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "type", "operator": "contains", "value": "Brand"}]}, "editable": True, "isPinned": True},
        ],
    ):
        with TestClient(app) as client:
            response = client.get("/vehicle_specifications?view=legacy")
    assert response.status_code == 200
    assert "Legacy Brands" in response.text


def test_brand_list_view_api_routes_support_create_update_delete_and_pin():
    Base.metadata.create_all(bind=engine)
    view = {"id": "legacy", "label": "Legacy Brands", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": True, "isPinned": False}
    updated = {**view, "label": "Global Brands", "isPinned": True}
    with patch("web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.create_view", return_value=view), patch(
        "web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.update_view", return_value=updated
    ), patch(
        "web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.delete_view", return_value=None
    ), patch(
        "web.backend.app.api.routers.vehicle_spec_router.LeadListViewService.set_pinned_view", return_value="legacy"
    ):
        with TestClient(app) as client:
            assert client.post("/vehicle_specifications/views", json={"label": "Legacy Brands"}).status_code == 200
            assert client.put("/vehicle_specifications/views/legacy", json={"label": "Global Brands"}).status_code == 200
            assert client.post("/vehicle_specifications/views/legacy/pin", json={"pinned": True}).status_code == 200
            assert client.delete("/vehicle_specifications/views/legacy").status_code == 200
