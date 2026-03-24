from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
from starlette.requests import Request
from unittest.mock import patch

from db.database import Base, engine
from web.backend.app.main import app
from web.backend.app.core.templates import templates


APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
OPPORTUNITY_LIST_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "opportunities" / "list_view.html"
OPPORTUNITY_DETAIL_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "opportunities" / "detail_view.html"
LIST_VIEW_JS = APP_ROOT / "web" / "frontend" / "static" / "js" / "list_views.js"


def build_request(path: str = "/opportunities/") -> Request:
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


def test_opportunity_list_template_contains_custom_list_view_controls():
    html = OPPORTUNITY_LIST_TEMPLATE.read_text()

    assert "opportunity-list-view-selector" in html
    assert "Customize Opportunity List View" in html
    assert "window.applyOpportunityListView(this.value)" in html
    assert "window.toggleOpportunityListViewPin()" in html
    assert "sf-list-view-icon--opportunity" in html
    assert "window.saveNewOpportunityListView()" in html
    assert "window.cloneOpportunityListView()" in html
    assert "window.deleteOpportunityListView()" in html
    assert "opportunity-view-filter-list" in html
    assert "opportunity-view-column-list" in html
    assert "d4_recent_opportunities" in html


def test_opportunity_detail_template_tracks_recently_viewed_records():
    html = OPPORTUNITY_DETAIL_TEMPLATE.read_text()

    assert "rememberRecentlyViewedRecord" in html
    assert "d4_recent_opportunities" in html
    assert '"/opportunities/" ~ record_id' in html
    assert "follow-btn" in html
    assert "toggleFollow('{{plural_type}}', '{{record_id}}'" in html


def test_list_view_assets_include_opportunity_list_logic():
    js = LIST_VIEW_JS.read_text()

    assert "initializeOpportunityListView" in js
    assert "applyOpportunityListView" in js
    assert "toggleOpportunityListViewPin" in js
    assert "saveNewOpportunityListView" in js
    assert "objectApiPath: \"/opportunities/views\"" in js


def test_opportunity_list_template_renders_with_default_list_view_context():
    html = templates.get_template("opportunities/list_view.html").render({
        "request": build_request(),
        "object_type": "Opportunity",
        "plural_type": "opportunities",
        "items": [],
        "columns": ["name", "amount", "stage", "model", "created"],
    })

    assert "opportunity-list-view-selector" in html
    assert "All Opportunities" in html
    assert "Setup" in html
    assert "Pin" in html


def test_opportunity_list_route_supports_saved_view_context():
    Base.metadata.create_all(bind=engine)
    with patch("web.backend.app.api.routers.opportunity_router.OpportunityService.get_opportunities", return_value=[]), patch(
        "web.backend.app.api.routers.opportunity_router.LeadListViewService.list_views",
        return_value=[
            {"id": "opp-all", "label": "All Opportunities", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "opp-recent", "label": "Recently Viewed", "source": "recent", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "warm-pipeline", "label": "Warm Pipeline", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "stage", "operator": "contains", "value": "Qualification"}]}, "editable": True, "isPinned": True},
        ],
    ):
        with TestClient(app) as client:
            response = client.get("/opportunities?view=warm-pipeline")

    assert response.status_code == 200
    assert "Warm Pipeline" in response.text
    assert "Customize Opportunity List View" in response.text
    assert "Pin" in response.text


def test_opportunity_list_view_api_routes_support_create_update_delete_and_pin():
    Base.metadata.create_all(bind=engine)
    created_view = {
        "id": "warm-pipeline",
        "label": "Warm Pipeline",
        "source": "all",
        "visibleColumns": ["name", "stage"],
        "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "stage", "operator": "contains", "value": "Qualification"}]},
        "editable": True,
        "isPinned": False,
    }
    updated_view = {**created_view, "label": "Closing Soon", "isPinned": True}

    with patch("web.backend.app.api.routers.opportunity_router.LeadListViewService.create_view", return_value=created_view), patch(
        "web.backend.app.api.routers.opportunity_router.LeadListViewService.update_view", return_value=updated_view
    ), patch(
        "web.backend.app.api.routers.opportunity_router.LeadListViewService.delete_view", return_value=None
    ), patch(
        "web.backend.app.api.routers.opportunity_router.LeadListViewService.set_pinned_view", return_value="warm-pipeline"
    ):
        with TestClient(app) as client:
            create_response = client.post("/opportunities/views", json={"label": "Warm Pipeline"})
            update_response = client.put("/opportunities/views/warm-pipeline", json={"label": "Closing Soon"})
            pin_response = client.post("/opportunities/views/warm-pipeline/pin", json={"pinned": True})
            delete_response = client.delete("/opportunities/views/warm-pipeline")

    assert create_response.status_code == 200
    assert create_response.json()["view"]["label"] == "Warm Pipeline"
    assert update_response.status_code == 200
    assert update_response.json()["view"]["label"] == "Closing Soon"
    assert pin_response.status_code == 200
    assert pin_response.json()["pinned_view_id"] == "warm-pipeline"
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"


def test_opportunity_follow_route_updates_follow_state():
    Base.metadata.create_all(bind=engine)

    with patch("web.backend.app.api.routers.opportunity_router.OpportunityService.toggle_follow", return_value=True):
        with TestClient(app) as client:
            response = client.post("/opportunities/opp-123/toggle-follow", data={"enabled": "true"})

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["followed"] is True


def test_opportunity_detail_related_lists_include_contact_product_asset_model_and_brand():
    Base.metadata.create_all(bind=engine)
    opportunity = SimpleNamespace(
        id="opp-1",
        name="Big Deal",
        stage="Prospecting",
        amount=300000,
        temperature="Warm",
        close_date=None,
        contact="contact-1",
        product="product-1",
        asset="asset-1",
        brand="brand-1",
        model="model-1",
        is_followed=False,
        created_at=None,
        updated_at=None,
    )
    contact = SimpleNamespace(id="contact-1", first_name="Jane", last_name="Doe", name="Jane Doe", email="jane@example.com", phone="01012345678")
    product = SimpleNamespace(id="product-1", name="EV Package", category="EV", base_price=550000)
    asset = SimpleNamespace(id="asset-1", name="Ioniq 5", vin="VIN123", status="Active")
    brand = SimpleNamespace(id="brand-1", name="Apex", record_type="Brand")
    model = SimpleNamespace(id="model-1", name="Ioniq 5", description="Mid-size EV")

    with patch("web.backend.app.api.routers.opportunity_router.OpportunityService.update_last_viewed", return_value=None), patch(
        "web.backend.app.api.routers.opportunity_router.OpportunityService.get_opportunity", return_value=opportunity
    ), patch(
        "web.backend.app.api.routers.opportunity_router.ContactService.get_contact", return_value=contact
    ), patch(
        "web.backend.app.api.routers.opportunity_router.ProductService.get_product", return_value=product
    ), patch(
        "web.backend.app.api.routers.opportunity_router.AssetService.get_asset", return_value=asset
    ), patch(
        "web.backend.app.api.routers.opportunity_router.BrandService.get_vehicle_spec", return_value=brand
    ), patch(
        "web.backend.app.api.routers.opportunity_router.ModelService.get_model", return_value=model
    ), patch(
        "web.backend.app.api.routers.opportunity_router.AIRecommendationService.normalize_temperature_label", return_value="Warm"
    ):
        with TestClient(app) as client:
            response = client.get("/opportunities/opp-1")

    assert response.status_code == 200
    assert "Contact" in response.text
    assert "Product" in response.text
    assert "Asset" in response.text
    assert "Model" in response.text
    assert "Brand" in response.text
    assert "/contacts/contact-1" in response.text
    assert "/products/product-1" in response.text
    assert "/assets/asset-1" in response.text
    assert "/models/model-1" in response.text
    assert "/vehicle_specifications/brand-1" in response.text
