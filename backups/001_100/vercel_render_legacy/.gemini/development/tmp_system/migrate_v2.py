import sqlite3
import os
import sys

# Add parent directory to path to import models and database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_PATH = "crm.db"

def migrate():
    print("🚀 Starting Extended Migration (Part 4)...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Add 'temperature' to 'opportunities'
        cursor.execute("PRAGMA table_info(opportunities)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'temperature' not in cols:
            print("Adding 'temperature' column to 'opportunities'...")
            cursor.execute("ALTER TABLE opportunities ADD COLUMN temperature TEXT")

        # 2. Add 'brand_id' to 'products' if not exists
        cursor.execute("PRAGMA table_info(products)")
        cols = [c[1] for c in cursor.fetchall()]
        if 'brand_id' not in cols:
            print("Adding 'brand_id' column to 'products'...")
            cursor.execute("ALTER TABLE products ADD COLUMN brand_id TEXT")

        # 3. Update Opportunity amounts based on Asset price
        print("Updating Opportunity amounts based on targeted Assets...")
        cursor.execute("""
            UPDATE opportunities 
            SET amount = (SELECT price FROM assets WHERE assets.id = opportunities.asset_id)
            WHERE asset_id IS NOT NULL AND asset_id != ''
        """)

        # 4. Map 'model_id' for Products (Update models FK if needed, but here we just ensure data mapping)
        print("Mapping existing Products to Models...")
        # Get one model to use as default if needed, or link by name if possible
        cursor.execute("SELECT id, name, brand_id FROM models LIMIT 1")
        default_model = cursor.fetchone()
        if default_model:
            cursor.execute("UPDATE products SET model_id = ?, brand_id = ? WHERE model_id IS NULL OR model_id = ''", (default_model[0], default_model[2]))

        # 5. Populate some temperatures for Opportunities
        print("Setting default temperatures for Opportunities...")
        cursor.execute("UPDATE opportunities SET temperature = 'Warm' WHERE temperature IS NULL OR temperature = ''")
        cursor.execute("UPDATE opportunities SET temperature = 'Hot' WHERE stage = 'Closed Won'")

        conn.commit()
        print("✨ Migration complete.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
