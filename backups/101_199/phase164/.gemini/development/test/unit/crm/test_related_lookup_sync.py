import pytest
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import Lead, Opportunity, Product, Model, VehicleSpecification
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.opportunity_service import OpportunityService

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

def test_lead_product_lookup_sync(db: Session):
    """Verify that selecting a product for a Lead syncs its Model and Brand."""
    try:
        # 1. Setup Data - Sequential commits to satisfy foreign keys
        brand = VehicleSpecification(id="SYNC_BRAND", name="Sync Brand", record_type="Brand")
        db.add(brand)
        db.commit()

        model = Model(id="SYNC_MODEL", name="Sync Model", brand="SYNC_BRAND")
        db.add(model)
        db.commit()

        product = Product(id="SYNC_PROD", name="Sync Product", model="SYNC_MODEL", brand="SYNC_BRAND")
        db.add(product)
        db.commit()

        # 2. Create Lead with only Product
        lead = LeadService.create_lead(db, first_name="Sync", last_name="Test", product="SYNC_PROD")
        
        # 3. Update Lead (triggering normalization)
        updated_lead = LeadService.update_lead(db, lead.id, product="SYNC_PROD")
        
        assert updated_lead.model == "SYNC_MODEL"
        assert updated_lead.brand == "SYNC_BRAND"

    finally:
        # Cleanup in reverse order
        db.query(Lead).filter(Lead.first_name == "Sync").delete()
        db.query(Product).filter(Product.id == "SYNC_PROD").delete()
        db.query(Model).filter(Model.id == "SYNC_MODEL").delete()
        db.query(VehicleSpecification).filter(VehicleSpecification.id == "SYNC_BRAND").delete()
        db.commit()

def test_opportunity_product_lookup_sync(db: Session):
    """Verify that selecting a product for an Opportunity syncs its Model and Brand."""
    try:
        # 1. Setup Data
        brand = VehicleSpecification(id="OPP_SYNC_BRAND", name="Opp Brand", record_type="Brand")
        db.add(brand)
        db.commit()

        model = Model(id="OPP_SYNC_MODEL", name="Opp Model", brand="OPP_SYNC_BRAND")
        db.add(model)
        db.commit()

        product = Product(id="OPP_SYNC_PROD", name="Opp Product", model="OPP_SYNC_MODEL", brand="OPP_SYNC_BRAND")
        db.add(product)
        db.commit()

        # 2. Create Opp
        opp = OpportunityService.create_opportunity(db, name="Sync Opp", product="OPP_SYNC_PROD")
        
        # 3. Update Opp (triggering normalization)
        updated_opp = OpportunityService.update_opportunity(db, opp.id, product="OPP_SYNC_PROD")
        
        assert updated_opp.model == "OPP_SYNC_MODEL"
        assert updated_opp.brand == "OPP_SYNC_BRAND"

    finally:
        db.query(Opportunity).filter(Opportunity.name == "Sync Opp").delete()
        db.query(Product).filter(Product.id == "OPP_SYNC_PROD").delete()
        db.query(Model).filter(Model.id == "OPP_SYNC_MODEL").delete()
        db.query(VehicleSpecification).filter(VehicleSpecification.id == "OPP_SYNC_BRAND").delete()
        db.commit()
