import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import random

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.models import Lead, Opportunity, VehicleSpecification, Product, Asset
from backend.app.database import SessionLocal

def map_data():
    db = SessionLocal()
    try:
        print("Starting data mapping for Phase 27...")
        
        # 1. Get available references
        brands = db.query(VehicleSpecification).filter(VehicleSpecification.record_type == "Brand").all()
        products = db.query(Product).all()
        assets = db.query(Asset).all()
        
        if not brands or not products or not assets:
            print("Warning: Missing Brands, Products, or Assets database records. Cannot map.")
            return

        # 2. Map Leads
        leads = db.query(Lead).filter(Lead.brand_id == None).all()
        print(f"Mapping {len(leads)} Leads...")
        for lead in leads:
            brand = random.choice(brands)
            # Find models for this brand
            models = db.query(VehicleSpecification).filter(
                VehicleSpecification.record_type == "Model",
                VehicleSpecification.parent_id == brand.id
            ).all()
            
            lead.brand_id = brand.id
            if models:
                lead.model_interest_id = random.choice(models).id
            
            # Pick a random product for now
            lead.product_id = random.choice(products).id
        
        # 3. Map Opportunities
        opps = db.query(Opportunity).filter(Opportunity.brand_id == None).all()
        print(f"Mapping {len(opps)} Opportunities...")
        for opp in opps:
            asset = random.choice(assets)
            opp.asset_id = asset.id
            opp.product_id = asset.product_id
            
            # Find brand/model for this product
            prod = db.query(Product).filter(Product.id == asset.product_id).first()
            if prod:
                opp.brand_id = prod.brand_id
                opp.model_interest_id = prod.model_id
        
        db.commit()
        print("Successfully mapped existing data!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during mapping: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    map_data()
