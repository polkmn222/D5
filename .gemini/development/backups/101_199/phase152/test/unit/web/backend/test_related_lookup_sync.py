import uuid

import pytest
from fastapi.testclient import TestClient

from db.database import Base, SessionLocal, engine
from web.backend.app.main import app
from web.backend.app.services.asset_service import AssetService
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _seed_vehicle_graph(db, suffix: str):
    brand = VehicleSpecService.create_spec(db, name=f"Brand-{suffix}", record_type="Brand")
    model = ModelService.create_model(db, name=f"Model-{suffix}", brand=brand.id, description=f"Model {suffix}")
    product = ProductService.create_product(
        db,
        name=f"Product-{suffix}",
        brand=brand.id,
        model=model.id,
        category="EV",
        base_price=55000000,
    )
    asset = AssetService.create_asset(
        db,
        name=f"Asset-{suffix}",
        product=product.id,
        brand=brand.id,
        model=model.id,
        vin=f"VIN-{suffix}",
        price=61000000,
    )
    return brand, model, product, asset


def test_lead_update_product_derives_model_and_brand(db):
    suffix = uuid.uuid4().hex[:6]
    brand, model, product, _asset = _seed_vehicle_graph(db, suffix)
    lead = LeadService.create_lead(db, first_name="Lead", last_name=suffix)

    updated = LeadService.update_lead(db, lead.id, product=product.id)

    assert updated.product == product.id
    assert updated.model == model.id
    assert updated.brand == brand.id


def test_lead_clearing_brand_clears_model_and_product(db):
    suffix = uuid.uuid4().hex[:6]
    brand, model, product, _asset = _seed_vehicle_graph(db, suffix)
    lead = LeadService.create_lead(
        db,
        first_name="Lead",
        last_name=suffix,
        brand=brand.id,
        model=model.id,
        product=product.id,
    )

    updated = LeadService.update_lead(db, lead.id, brand=None, _force_null_fields=["brand"])

    assert updated.brand is None
    assert updated.model is None
    assert updated.product is None


def test_opportunity_update_product_derives_parent_lookups_and_clears_asset(db):
    suffix = uuid.uuid4().hex[:6]
    brand_a, model_a, product_a, asset_a = _seed_vehicle_graph(db, f"a-{suffix}")
    brand_b, model_b, product_b, _asset_b = _seed_vehicle_graph(db, f"b-{suffix}")
    opportunity = OpportunityService.create_opportunity(
        db,
        name=f"Deal-{suffix}",
        brand=brand_a.id,
        model=model_a.id,
        product=product_a.id,
        asset=asset_a.id,
    )

    updated = OpportunityService.update_opportunity(db, opportunity.id, product=product_b.id)

    assert updated.product == product_b.id
    assert updated.model == model_b.id
    assert updated.brand == brand_b.id
    assert updated.asset is None


def test_opportunity_clearing_brand_clears_model_product_and_asset(db):
    suffix = uuid.uuid4().hex[:6]
    brand, model, product, asset = _seed_vehicle_graph(db, suffix)
    opportunity = OpportunityService.create_opportunity(
        db,
        name=f"Deal-{suffix}",
        brand=brand.id,
        model=model.id,
        product=product.id,
        asset=asset.id,
    )

    updated = OpportunityService.update_opportunity(db, opportunity.id, brand=None, _force_null_fields=["brand"])

    assert updated.brand is None
    assert updated.model is None
    assert updated.product is None
    assert updated.asset is None


def test_lead_detail_related_cards_reflect_lookup_removal(db):
    suffix = uuid.uuid4().hex[:6]
    _brand, _model, product, _asset = _seed_vehicle_graph(db, suffix)
    lead = LeadService.create_lead(db, first_name="Lead", last_name=suffix, product=product.id)
    LeadService.update_lead(db, lead.id, product=product.id)

    with TestClient(app) as client:
        response = client.get(f"/leads/{lead.id}")
        assert response.status_code == 200
        assert product.name in response.text

        LeadService.update_lead(db, lead.id, brand=None, _force_null_fields=["brand"])

        updated_response = client.get(f"/leads/{lead.id}")
        assert updated_response.status_code == 200
        assert product.name not in updated_response.text
        assert "No related records found." in updated_response.text


def test_opportunity_detail_related_section_includes_linked_lead(db):
    suffix = uuid.uuid4().hex[:6]
    lead = LeadService.create_lead(db, first_name="Casey", last_name=f"Lead-{suffix}", email=f"lead-{suffix}@test.com")
    opportunity = OpportunityService.create_opportunity(db, name=f"Deal-{suffix}", lead=lead.id)

    with TestClient(app) as client:
        response = client.get(f"/opportunities/{opportunity.id}")

    assert response.status_code == 200
    assert "Lead" in response.text
    assert f"Casey Lead-{suffix}" in response.text
