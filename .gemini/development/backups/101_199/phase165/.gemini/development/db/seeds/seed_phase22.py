import os
import sys
import random
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Ensure we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db.models import Lead, Contact, Opportunity, Asset, Product
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.timezone import get_kst_now_naive

def seed_data():
    db = SessionLocal()
    
    first_names = ["Oliver", "Emma", "Liam", "Ava", "Noah", "Sophia", "Lucas", "Isabella", "Mason", "Mia", "Ethan"]
    last_names = ["Wilson", "Taylor", "Anderson", "Thomas", "Moore", "Jackson", "White", "Harris", "Clark", "Lewis"]
    domains = ["gk-auto.com", "global-solutions.kr", "premium-service.net", "tech-hub.io"]
    
    print("Seeding 10 Leads for Phase 22...")
    for i in range(10):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        lead = Lead(
            id=get_id("Lead"),
            first_name=fn,
            last_name=ln,
            email=f"{fn.lower()}.{ln.lower()}@{random.choice(domains)}",
            phone=f"010-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            status=random.choice(["New", "Open", "Working", "Qualified"]),
            gender=random.choice(["Male", "Female", "Other"]),
            description="Phase 22 Test Data",
            created_at=get_kst_now_naive(),
            updated_at=get_kst_now_naive()
        )
        db.add(lead)

    print("Seeding 10 Contacts for Phase 22...")
    contacts = []
    for i in range(10):
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        contact = Contact(
            id=get_id("Contact"),
            first_name=fn,
            last_name=ln,
            name=f"{fn} {ln}",
            email=f"{fn.lower()}.{ln.lower()}@{random.choice(domains)}",
            phone=f"010-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            gender=random.choice(["Male", "Female", "Other"]),
            created_at=get_kst_now_naive(),
            updated_at=get_kst_now_naive()
        )
        db.add(contact)
        db.flush()
        contacts.append(contact)

    print("Seeding 10 Opportunities for Phase 22...")
    for i in range(10):
        contact = random.choice(contacts)
        opp = Opportunity(
            id=get_id("Opportunity"),
            contact=contact.id,
            name=f"Project {random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])} - {contact.name}",
            amount=random.randint(5000000, 50000000), # KRW
            stage=random.choice(["Prospecting", "Qualification", "Needs Analysis", "Value Proposition", "Closed Won", "Closed Lost"]),
            status="Open",
            probability=random.randint(10, 90),
            close_date=(get_kst_now_naive() + timedelta(days=random.randint(30, 180))).date(),
            created_at=get_kst_now_naive(),
            updated_at=get_kst_now_naive()
        )
        db.add(opp)

    print("Seeding 10 Products for Phase 22...")
    products = []
    for i in range(10):
        prod = Product(
            id=get_id("Product"),
            name=f"GK Model {random.choice(['X', 'Y', 'S', '3'])} v{i+1}",
            description="Premium test product",
            base_price=random.randint(40000000, 120000000),
            created_at=get_kst_now_naive(),
            updated_at=get_kst_now_naive()
        )
        db.add(prod)
        db.flush()
        products.append(prod)

    print("Seeding 10 Assets for Phase 22...")
    for i in range(10):
        contact = random.choice(contacts)
        prod = random.choice(products)
        asset = Asset(
            id=get_id("Asset"),
            contact=contact.id,
            product=prod.id,
            name=f"{prod.name} - {contact.name}",
            vin=f"KMH{random.randint(100000, 999999)}A{random.randint(100000, 999999)}",
            status=random.choice(["Ordered", "In Transit", "Delivered"]),
            purchase_date=(get_kst_now_naive() - timedelta(days=random.randint(10, 100))).date(),
            created_at=get_kst_now_naive(),
            updated_at=get_kst_now_naive()
        )
        db.add(asset)

    db.commit()
    print("Phase 22 Seeding complete (Account/Campaign removed).")

if __name__ == "__main__":
    seed_data()
