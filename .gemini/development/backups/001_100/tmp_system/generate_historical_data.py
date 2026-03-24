import sqlite3
import random
import uuid
from datetime import datetime, timedelta

DB_PATH = "crm.db"

def get_id(prefix):
    return f"{prefix}_{str(uuid.uuid4())[:14]}"

def generate_random_date():
    # 40% chance for a very recent date (last 25 days) to ensure dashboard bars are visible
    if random.random() < 0.4:
        days_back = random.randint(0, 25)
    else:
        days_back = random.randint(0, 730)
    return (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d %H:%M:%S")

def populate_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get existing IDs for associations
        cursor.execute("SELECT id FROM vehicle_specifications WHERE record_type = 'Brand'")
        brands = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("SELECT id, brand_id FROM models")
        models = cursor.fetchall() # (id, brand_id)
        
        cursor.execute("SELECT id, model_id FROM products")
        products = cursor.fetchall() # (id, model_id)
        
        cursor.execute("SELECT id FROM assets")
        assets = [r[0] for r in cursor.fetchall()]

        # 1. Accounts (10 more)
        account_ids = []
        for i in range(10):
            acc_id = f"001{str(uuid.uuid4())[:15]}"
            name = f"Global Tech {i+21}"
            date = generate_random_date()
            cursor.execute("INSERT INTO accounts (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)", 
                         (acc_id, name, date, date))
            account_ids.append(acc_id)

        # 2. Contacts (10 more)
        contact_statuses = ["New", "Working", "Nurturing", "Closed"]
        for i in range(10):
            ct_id = f"003{str(uuid.uuid4())[:15]}"
            first = random.choice(["James", "Mary", "Robert", "Patricia", "John", "Jennifer"])
            last = random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones"])
            status = random.choice(contact_statuses)
            date = generate_random_date()
            acc_id = random.choice(account_ids)
            cursor.execute("""
                INSERT INTO contacts (id, account_id, first_name, last_name, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ct_id, acc_id, first, last, status, date, date))

        # 3. Opportunities (10 more - diverse stages)
        stages = ["Qualification", "Discovery", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"]
        temps = ["Hot", "Warm", "Cold"]
        for i in range(10):
            opp_id = f"006{str(uuid.uuid4())[:15]}"
            name = f"Strategic Deal {i+21}"
            stage = random.choice(stages)
            temp = random.choice(temps)
            amount = random.randint(50000000, 200000000)
            date = generate_random_date()
            acc_id = random.choice(account_ids)
            
            cursor.execute("""
                INSERT INTO opportunities (id, account_id, name, stage, amount, temperature, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (opp_id, acc_id, name, stage, amount, temp, date, date))

        # 4. Assets (20 more)
        for i in range(20):
            asset_id = f"02i{str(uuid.uuid4())[:15]}"
            name = f"Vehicle {random.randint(1000, 9999)} {random.choice(['XL', 'SE', 'Limited'])}"
            price = random.randint(30000000, 150000000)
            date = generate_random_date()
            acc_id = random.choice(account_ids) # Use a randomly generated account from step 1
            cursor.execute("""
                INSERT INTO assets (id, account_id, name, price, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (asset_id, acc_id, name, price, date, date))

        conn.commit()
        print("Successfully generated additional 10 Accounts, 10 Contacts, 10 Opportunities, and 20 Assets.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    populate_data()
