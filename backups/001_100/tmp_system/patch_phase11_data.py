import sys
import os
import random
import string
from sqlalchemy.orm import Session

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.database import SessionLocal
from backend.app.models import Product, Asset

def generate_random_vin(length=18):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def patch_data():
    db = SessionLocal()
    try:
        # Patch Product prices: round down to nearest 1,000
        products = db.query(Product).all()
        print(f"[DEBUG] Found {len(products)} products to patch.")
        for prod in products:
            if prod.base_price:
                old_price = prod.base_price
                new_price = (old_price // 1000) * 1000
                if old_price != new_price:
                    prod.base_price = new_price
                    print(f"  [PRODUCT] {prod.name}: {old_price} -> {new_price}")
        
        # Patch Asset VINs: 18-character random alphanumeric
        assets = db.query(Asset).all()
        print(f"[DEBUG] Found {len(assets)} assets to patch.")
        for asset in assets:
            old_vin = asset.vin
            new_vin = generate_random_vin(18)
            asset.vin = new_vin
            print(f"  [ASSET] {asset.name}: {old_vin} -> {new_vin}")
            
        db.commit()
        print("[DEBUG] Patch completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Patch failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    patch_data()
