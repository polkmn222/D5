from pathlib import Path

from fastapi.testclient import TestClient
from starlette.requests import Request
from unittest.mock import patch

from db.database import Base, engine
from web.backend.app.main import app
from web.backend.app.core.templates import templates


APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
PRODUCT_LIST_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "products" / "list_view.html"
PRODUCT_DETAIL_TEMPLATE = APP_ROOT / "web" / "frontend" / "templates" / "products" / "detail_view.html"
LIST_VIEW_JS = APP_ROOT / "web" / "frontend" / "static" / "js" / "list_views.js"


def build_request(path: str = "/products/") -> Request:
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


def test_product_list_template_contains_custom_list_view_controls():
    html = PRODUCT_LIST_TEMPLATE.read_text()

    assert "product-list-view-selector" in html
    assert "Customize Product List View" in html
    assert "window.applyProductListView(this.value)" in html
    assert "window.toggleProductListViewPin()" in html
    assert "sf-list-view-icon--product" in html
    assert "window.saveNewProductListView()" in html
    assert "product-view-filter-list" in html
    assert "product-view-column-list" in html
    assert "d4_recent_products" in html


def test_product_detail_template_tracks_recently_viewed_records():
    html = PRODUCT_DETAIL_TEMPLATE.read_text()

    assert "rememberRecentlyViewedRecord" in html
    assert "d4_recent_products" in html
    assert '"/products/" ~ record_id' in html


def test_list_view_assets_include_product_list_logic():
    js = LIST_VIEW_JS.read_text()

    assert "initializeProductListView" in js
    assert "applyProductListView" in js
    assert "toggleProductListViewPin" in js
    assert "saveNewProductListView" in js
    assert "objectApiPath: \"/products/views\"" in js


def test_product_list_template_renders_with_default_list_view_context():
    html = templates.get_template("products/list_view.html").render({
        "request": build_request(),
        "object_type": "Product",
        "plural_type": "products",
        "items": [],
        "columns": ["name", "brand", "model", "base_price", "category"],
    })

    assert "product-list-view-selector" in html
    assert "All Products" in html
    assert "Setup" in html
    assert "Pin" in html


def test_product_list_template_shows_pagination_controls_when_present():
    html = templates.get_template("products/list_view.html").render({
        "request": build_request(),
        "object_type": "Product",
        "plural_type": "products",
        "items": [],
        "columns": ["name", "brand", "model", "base_price", "category"],
        "pagination": {"page": 2, "total_pages": 4, "total_items": 160, "has_prev": True, "has_next": True, "prev_page": 1, "next_page": 3},
        "current_view": "product-all",
    })

    assert "Page 2 of 4" in html
    assert "Previous" in html
    assert "Next" in html


def test_product_list_route_supports_saved_view_context():
    Base.metadata.create_all(bind=engine)
    with patch("web.backend.app.api.routers.product_router.is_feature_enabled", return_value=True), patch(
        "web.backend.app.api.routers.product_router.ProductService.get_products", return_value=[]
    ), patch(
        "web.backend.app.api.routers.product_router.LeadListViewService.list_views",
        return_value=[
            {"id": "product-all", "label": "All Products", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "product-recent", "label": "Recently Viewed", "source": "recent", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": []}, "editable": False, "isPinned": False},
            {"id": "catalog", "label": "SUV Catalog", "source": "all", "visibleColumns": ["name"], "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "category", "operator": "contains", "value": "SUV"}]}, "editable": True, "isPinned": True},
        ],
    ):
        with TestClient(app) as client:
            response = client.get("/products?view=catalog")

    assert response.status_code == 200
    assert "SUV Catalog" in response.text
    assert "Customize Product List View" in response.text


def test_product_list_view_api_routes_support_create_update_delete_and_pin():
    Base.metadata.create_all(bind=engine)
    created_view = {
        "id": "catalog",
        "label": "SUV Catalog",
        "source": "all",
        "visibleColumns": ["name", "category"],
        "filters": {"searchTerm": "", "logic": "and", "conditions": [{"field": "category", "operator": "contains", "value": "SUV"}]},
        "editable": True,
        "isPinned": False,
    }
    updated_view = {**created_view, "label": "Sedan Catalog", "isPinned": True}

    with patch("web.backend.app.api.routers.product_router.LeadListViewService.create_view", return_value=created_view), patch(
        "web.backend.app.api.routers.product_router.LeadListViewService.update_view", return_value=updated_view
    ), patch(
        "web.backend.app.api.routers.product_router.LeadListViewService.delete_view", return_value=None
    ), patch(
        "web.backend.app.api.routers.product_router.LeadListViewService.set_pinned_view", return_value="catalog"
    ), patch("web.backend.app.api.routers.product_router.is_feature_enabled", return_value=True):
        with TestClient(app) as client:
            create_response = client.post("/products/views", json={"label": "SUV Catalog"})
            update_response = client.put("/products/views/catalog", json={"label": "Sedan Catalog"})
            pin_response = client.post("/products/views/catalog/pin", json={"pinned": True})
            delete_response = client.delete("/products/views/catalog")

    assert create_response.status_code == 200
    assert update_response.status_code == 200
    assert pin_response.status_code == 200
    assert delete_response.status_code == 200


def test_product_detail_template_supports_salesforce_style_related_cards():
    html = PRODUCT_DETAIL_TEMPLATE.read_text()

    assert "sf-related-card" in html
    assert "View All" in html
    assert "sf-related-icon sf-related-icon--{{ list.icon }}" in html
