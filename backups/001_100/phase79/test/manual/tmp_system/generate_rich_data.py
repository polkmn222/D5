import random
import string
from datetime import datetime, timedelta
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[3]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from test.manual._runtime import bootstrap_runtime, should_reset_database

engine, SessionLocal, Base = bootstrap_runtime()
from db.models import Contact, Lead, Opportunity, Product, VehicleSpecification, Model

def get_id(prefix):
    chars = string.ascii_letters + string.digits
    res = ''.join(random.choice(chars) for _ in range(15))
    return f"{prefix[:3].upper()}{res}"

def get_kst_now():
    return datetime.utcnow() + timedelta(hours=9)

def generate_rich_test_data():
    if should_reset_database():
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    print("Generating 10 rich Leads and 10 rich Opportunities...")
    now = get_kst_now()

    try:
        brands = db.query(VehicleSpecification).filter(VehicleSpecification.record_type == "Brand").all()
        models = db.query(Model).all()
        products = db.query(Product).all()
        contacts = db.query(Contact).all()

        if not contacts:
            for index in range(5):
                db.add(
                    Contact(
                        id=get_id("Con"),
                        first_name=f"Seed{index}",
                        last_name="Contact",
                        email=f"seed{index}@example.com",
                        phone=f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                    )
                )
            db.commit()
            contacts = db.query(Contact).all()

        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "David", "Elizabeth"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        stages = ["Prospecting", "Qualification", "Needs Analysis", "Proposal", "Closed Won", "Closed Lost"]

        for index in range(10):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            product = random.choice(products) if products else None
            brand = random.choice(brands) if brands else None
            model = random.choice(models) if models else None

            db.add(
                Lead(
                    id=get_id("Lead"),
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{first_name.lower()}.{last_name.lower()}{random.randint(100,999)}@rich-test.com",
                    phone=f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                    status=random.choice(["New", "Follow Up", "Qualified"]),
                    brand=brand.id if brand else None,
                    model=model.id if model else None,
                    product=product.id if product else None,
                    is_converted=False,
                    is_followed=False,
                    created_at=now - timedelta(days=random.randint(0, 3)),
                    updated_at=now,
                )
            )

        for index in range(10):
            product = random.choice(products) if products else None
            brand = random.choice(brands) if brands else None
            model = random.choice(models) if models else None
            contact = random.choice(contacts)

            db.add(
                Opportunity(
                    id=get_id("Opp"),
                    contact=contact.id,
                    product=product.id if product else None,
                    brand=brand.id if brand else None,
                    model=model.id if model else None,
                    name=f"Super Deal {index + 1}",
                    amount=random.randint(80000000, 300000000),
                    stage=random.choice(stages),
                    temperature=random.choice(["Hot", "Warm", "Cold"]),
                    status="Open",
                    is_followed=False,
                    created_at=now - timedelta(days=random.randint(0, 3)),
                    updated_at=now,
                )
            )

        db.commit()
        print("Rich test data generation complete.")
    finally:
        db.close()


if __name__ == "__main__":
    generate_rich_test_data()
