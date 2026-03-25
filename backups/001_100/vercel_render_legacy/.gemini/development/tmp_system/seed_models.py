import sys
import os
import random

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal
from backend.app.models import Model, Lead, Opportunity, Asset, VehicleSpecification
from backend.app.utils.sf_id import get_id

def seed_models():
    db = SessionLocal()
    try:
        # Get existing brands
        brands = db.query(VehicleSpecification).filter(VehicleSpecification.record_type == "Brand").all()
        if not brands:
            print("No brands found. Creating a default brand.")
            brand = VehicleSpecification(id=get_id("Brand"), name="General Motors", record_type="Brand")
            db.add(brand)
            db.commit()
            brands = [brand]

        model_names = ["Model S", "Model 3", "Model X", "Model Y", "Taycan", "911 Carrera", "Ioniq 5", "EV6", "Bolt EV", "Leaf Plus"]
        created_models = []

        for name in model_names:
            model = Model(
                id=get_id("Model"),
                name=name,
                brand_id=random.choice(brands).id,
                description=f"High-performance vehicle model: {name}"
            )
            db.add(model)
            created_models.append(model)
        
        db.commit()
        print(f"Created {len(created_models)} models.")

        # Map to Leads
        leads = db.query(Lead).all()
        for l in leads:
            l.model_id = random.choice(created_models).id
        
        # Map to Opportunities
        opps = db.query(Opportunity).all()
        for o in opps:
            o.model_id = random.choice(created_models).id
            
        # Map to Assets
        assets = db.query(Asset).all()
        for a in assets:
            a.model_id = random.choice(created_models).id

        db.commit()
        print("Mapped models to Leads, Opportunities, and Assets.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding models: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_models()
