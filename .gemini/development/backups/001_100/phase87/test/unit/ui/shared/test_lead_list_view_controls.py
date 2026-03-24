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

    assert "lead-list-view-selector" in html
    assert "Recently Viewed" in html
    assert "window.applyLeadListView(this.value)" in html
    assert "window.refreshLeadListView()" in html
    assert "lead-list-actions-dropdown" in html
    assert "lead-empty-state" in html
    assert "data-record-id=" in html


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
    assert ".sf-list-view-controls" in css
    assert ".sf-list-view-empty" in css


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


def test_lead_list_route_supports_recent_view_query_param():
    Base.metadata.create_all(bind=engine)
    with patch("web.backend.app.api.routers.lead_router.LeadService.get_leads", return_value=[]):
        with TestClient(app) as client:
            response = client.get("/leads?view=recent")

    assert response.status_code == 200
    assert 'data-current-view="recent"' in response.text
    assert "Recently Viewed" in response.text
