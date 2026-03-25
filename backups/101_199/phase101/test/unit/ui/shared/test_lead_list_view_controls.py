from pathlib import Path

from fastapi.testclient import TestClient
from starlette.requests import Request
from unittest.mock import patch

from db.database import Base, engine
from web.backend.app.main import app
from web.backend.app.core.templates import templates


APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
LEAD_LIST_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "leads" / "list_view.html"
LEAD_DETAIL_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "leads" / "detail_view.html"
LIST_VIEW_JS = APP_ROOT / "web" / "frontend" / "static" / "js" / "list_views.js"
LIST_VIEW_CSS = APP_ROOT / "web" / "frontend" / "static" / "css" / "list_views.css"


def build_request(path: str = "/leads/") -> Request:
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


def test_lead_list_template_contains_all_and_recent_controls():
    html = LEAD_LIST_TEMPLATE.read_text()

    assert "sf-list-view-page-header" in html
    assert "sf-list-view-hero-row" in html
    assert "lead-list-view-selector" in html
    assert "lead-list-pin-btn" in html
    assert "Recently Viewed" in html
    assert "window.applyLeadListView(this.value)" in html
    assert "window.refreshLeadListView()" in html
    assert "lead-list-setup-dropdown" in html
    assert "Customize List View" in html
    assert "Save as New" in html
    assert "Save Changes" in html
    assert "Clone" in html
    assert "Data source" in html
    assert "Contains text" in html
    assert "Filter logic" in html
    assert "Filter conditions" in html
    assert "lead-view-filter-list" in html
    assert "Add Filter" in html
    assert "lead-view-column-list" in html
    assert "draggable=\"true\"" in html
    assert "lead-empty-state" in html
    assert "data-record-id=" in html
    assert "data-column-key=" in html


def test_lead_detail_template_tracks_recently_viewed_records():
    html = LEAD_DETAIL_TEMPLATE.read_text()

    assert "rememberRecentlyViewedRecord" in html
    assert "d4_recent_leads" in html
    assert '"/leads/" ~ record_id' in html


def test_list_view_assets_include_recent_view_logic():
    js = LIST_VIEW_JS.read_text()
    css = LIST_VIEW_CSS.read_text()

    assert "rememberRecentlyViewedRecord" in js
    assert "initializeLeadListView" in js
    assert "readRecentListViewRecords" in js
    assert "normalizeLeadListView" in js
    assert "requestLeadListView" in js
    assert "confirmLeadListAction" in js
    assert "saveLeadListViewLayout" in js
    assert "saveNewLeadListView" in js
    assert "cloneLeadListView" in js
    assert "deleteLeadListView" in js
    assert "toggleLeadListViewPin" in js
    assert "addLeadListViewFilterCondition" in js
    assert "removeLeadListViewFilterCondition" in js
    assert 'querySelectorAll(".sf-list-view-column-item")' in js
    assert ".sf-list-view-controls" in css
    assert ".sf-list-view-empty" in css
    assert ".sf-list-view-page-header" in css
    assert ".sf-list-view-setup-menu" in css
    assert ".sf-list-view-selector" in css
    assert ".sf-list-view-search-tools" in css
    assert ".sf-list-view-column-item" in css
    assert ".sf-list-view-pin.is-pinned" in css
    assert ".sf-list-view-filter-row" in css
    assert ".sf-list-view-add-filter" in css


def test_lead_list_template_renders_with_default_list_view_context():
    html = templates.get_template("leads/list_view.html").render({
        "request": build_request(),
        "object_type": "Lead",
        "plural_type": "leads",
        "items": [],
        "columns": ["name"],
    })

    assert "lead-list-view-selector" in html
    assert "d4_recent_leads" in html
    assert "All Leads" in html
    assert "Setup" in html
    assert "Save as New" in html
    assert "Pin" in html
    assert "Match all conditions" in html


def test_lead_list_route_supports_recent_view_query_param():
    Base.metadata.create_all(bind=engine)
    with patch("web.backend.app.api.routers.lead_router.LeadService.get_leads", return_value=[]), patch(
        "web.backend.app.api.routers.lead_router.LeadListViewService.list_views",
        return_value=[
            {"id": "all", "label": "All Leads", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "recent", "label": "Recently Viewed", "source": "recent", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "custom-open", "label": "Open Leads", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "status", "operator": "equals", "value": "New"}]}, "editable": True, "isPinned": True},
        ],
    ):
        with TestClient(app) as client:
            response = client.get("/leads?view=custom-open")

    assert response.status_code == 200
    assert "Open Leads" in response.text
    assert "Setup" in response.text
    assert "Customize List View" in response.text
    assert "Pin" in response.text


def test_lead_list_view_api_routes_support_create_update_delete_and_pin():
    Base.metadata.create_all(bind=engine)
    created_view = {
        "id": "custom-open",
        "label": "Open Leads",
        "source": "all",
        "visibleColumns": ["name", "status"],
        "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "status", "operator": "equals", "value": "New"}]},
        "editable": True,
        "isPinned": False,
    }
    updated_view = {
        **created_view,
        "label": "Fresh Leads",
        "isPinned": True,
    }

    with patch("web.backend.app.api.routers.lead_router.LeadListViewService.create_view", return_value=created_view), patch(
        "web.backend.app.api.routers.lead_router.LeadListViewService.update_view", return_value=updated_view
    ), patch(
        "web.backend.app.api.routers.lead_router.LeadListViewService.delete_view", return_value=None
    ), patch(
        "web.backend.app.api.routers.lead_router.LeadListViewService.set_pinned_view", return_value="custom-open"
    ):
        with TestClient(app) as client:
            create_response = client.post("/leads/views", json={"label": "Open Leads"})
            update_response = client.put("/leads/views/custom-open", json={"label": "Fresh Leads"})
            pin_response = client.post("/leads/views/custom-open/pin", json={"pinned": True})
            delete_response = client.delete("/leads/views/custom-open")

    assert create_response.status_code == 200
    assert create_response.json()["view"]["label"] == "Open Leads"
    assert update_response.status_code == 200
    assert update_response.json()["view"]["label"] == "Fresh Leads"
    assert pin_response.status_code == 200
    assert pin_response.json()["pinned_view_id"] == "custom-open"
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"
