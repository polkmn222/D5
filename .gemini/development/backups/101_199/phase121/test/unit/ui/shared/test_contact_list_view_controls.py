from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from starlette.requests import Request
from unittest.mock import patch

from db.database import Base, engine
from web.backend.app.main import app
from web.backend.app.core.templates import templates


APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
CONTACT_LIST_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "contacts" / "list_view.html"
CONTACT_DETAIL_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "contacts" / "detail_view.html"
LIST_VIEW_JS = APP_ROOT / "web" / "frontend" / "static" / "js" / "list_views.js"


def build_request(path: str = "/contacts/") -> Request:
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


def test_contact_list_template_contains_custom_list_view_controls():
    html = CONTACT_LIST_TEMPLATE.read_text()

    assert "contact-list-view-selector" in html
    assert "Customize Contact List View" in html
    assert "window.applyContactListView(this.value)" in html
    assert "window.toggleContactListViewPin()" in html
    assert "sf-list-view-icon--contact" in html
    assert "window.saveNewContactListView()" in html
    assert "window.cloneContactListView()" in html
    assert "window.deleteContactListView()" in html
    assert "contact-view-filter-list" in html
    assert "contact-view-column-list" in html
    assert "d4_recent_contacts" in html


def test_contact_detail_template_tracks_recently_viewed_records():
    html = CONTACT_DETAIL_TEMPLATE.read_text()

    assert "rememberRecentlyViewedRecord" in html
    assert "d4_recent_contacts" in html
    assert '"/contacts/" ~ record_id' in html


def test_list_view_assets_include_contact_list_logic():
    js = LIST_VIEW_JS.read_text()

    assert "initializeContactListView" in js
    assert "applyContactListView" in js
    assert "toggleContactListViewPin" in js
    assert "saveNewContactListView" in js
    assert "requestLeadListView(\"/contacts/views\"" in js or "objectApiPath: \"/contacts/views\"" in js


def test_contact_list_template_renders_with_default_list_view_context():
    html = templates.get_template("contacts/list_view.html").render({
        "request": build_request(),
        "object_type": "Contact",
        "plural_type": "contacts",
        "items": [],
        "columns": ["name", "email", "phone", "tier", "created"],
    })

    assert "contact-list-view-selector" in html
    assert "All Contacts" in html
    assert "Setup" in html
    assert "Pin" in html


def test_contact_list_route_supports_saved_view_context():
    Base.metadata.create_all(bind=engine)
    with patch("web.backend.app.api.routers.contact_router.ContactService.get_contacts", return_value=[]), patch(
        "web.backend.app.api.routers.contact_router.LeadListViewService.list_views",
        return_value=[
            {"id": "all", "label": "All Contacts", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "recent", "label": "Recently Viewed", "source": "recent", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "vip", "label": "VIP Contacts", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "tier", "operator": "contains", "value": "Gold"}]}, "editable": True, "isPinned": True},
        ],
    ):
        with TestClient(app) as client:
            response = client.get("/contacts?view=vip")

    assert response.status_code == 200
    assert "VIP Contacts" in response.text
    assert "Customize Contact List View" in response.text
    assert "Pin" in response.text


def test_contact_list_view_api_routes_support_create_update_delete_and_pin():
    Base.metadata.create_all(bind=engine)
    created_view = {
        "id": "vip",
        "label": "VIP Contacts",
        "source": "all",
        "visibleColumns": ["name", "tier"],
        "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "tier", "operator": "contains", "value": "Gold"}]},
        "editable": True,
        "isPinned": False,
    }
    updated_view = {**created_view, "label": "Warm Contacts", "isPinned": True}

    with patch("web.backend.app.api.routers.contact_router.LeadListViewService.create_view", return_value=created_view), patch(
        "web.backend.app.api.routers.contact_router.LeadListViewService.update_view", return_value=updated_view
    ), patch(
        "web.backend.app.api.routers.contact_router.LeadListViewService.delete_view", return_value=None
    ), patch(
        "web.backend.app.api.routers.contact_router.LeadListViewService.set_pinned_view", return_value="vip"
    ):
        with TestClient(app) as client:
            create_response = client.post("/contacts/views", json={"label": "VIP Contacts"})
            update_response = client.put("/contacts/views/vip", json={"label": "Warm Contacts"})
            pin_response = client.post("/contacts/views/vip/pin", json={"pinned": True})
            delete_response = client.delete("/contacts/views/vip")

    assert create_response.status_code == 200
    assert create_response.json()["view"]["label"] == "VIP Contacts"
    assert update_response.status_code == 200
    assert update_response.json()["view"]["label"] == "Warm Contacts"
    assert pin_response.status_code == 200
    assert pin_response.json()["pinned_view_id"] == "vip"
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"


def test_contact_detail_related_lists_include_opportunities_messages_and_assets():
    Base.metadata.create_all(bind=engine)
    contact = SimpleNamespace(
        id="contact-1",
        first_name="Jane",
        last_name="Doe",
        name="Jane Doe",
        email="jane@example.com",
        phone="01012345678",
        website="",
        tier="Gold",
        created_at=None,
        updated_at=None,
    )
    opportunities = [SimpleNamespace(id="opp-1", name="Deal One", stage="Prospecting", amount=120000)]
    messages = [SimpleNamespace(id="msg-1", content="Follow-up text message sent to customer", direction="Outbound", status="Sent")]
    assets = [SimpleNamespace(id="asset-1", name="Ioniq 5", vin="VIN123", status="Active")]

    with patch("web.backend.app.api.routers.contact_router.ContactService.get_contact", return_value=contact), patch(
        "web.backend.app.api.routers.contact_router.OpportunityService.get_by_contact", return_value=opportunities
    ), patch(
        "web.backend.app.api.routers.contact_router.MessageService.get_messages", return_value=messages
    ), patch(
        "web.backend.app.api.routers.contact_router.AssetService.get_assets", return_value=assets
    ):
        with TestClient(app) as client:
            response = client.get("/contacts/contact-1")

    assert response.status_code == 200
    assert "Opportunities" in response.text
    assert "Messages" in response.text
    assert "Assets" in response.text
    assert "View All" in response.text
    assert "/opportunities/opp-1" in response.text
    assert "/messages/msg-1" in response.text
    assert "/assets/asset-1" in response.text
