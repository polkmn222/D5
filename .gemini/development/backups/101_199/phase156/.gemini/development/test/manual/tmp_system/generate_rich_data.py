import sqlite3
import random
import string
from datetime import datetime, timedelta

db_path = "/Users/sangyeol.park@gruve.ai/D4/crm.db"

def get_id(prefix):
    chars = string.ascii_letters + string.digits
    res = ''.join(random.choice(chars) for _ in range(15))
    return f"{prefix[:3].upper()}{res}"

def get_kst_now():
    return datetime.utcnow() + timedelta(hours=9)

def generate_rich_test_data():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("Generating 10 rich Leads and 10 rich Opportunities...")
    now = get_kst_now()

    # Get available Brand, Model, Product, Account
    cur.execute("SELECT id FROM vehicle_specifications WHERE record_type = 'Brand'")
    brand_ids = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT id, brand_id FROM models")
    models = cur.fetchall() # list of (id, brand_id)
    
    cur.execute("SELECT id, brand_id, model_id FROM products")
    products = cur.fetchall() # list of (id, brand_id, model_id)
    
    cur.execute("SELECT id FROM accounts")
    account_ids = [row[0] for row in cur.fetchall()]

    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "David", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    stages = ["Qualification", "Test Drive", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"]

    # 1. Generate 10 Rich Leads (Recent)
    for i in range(10):
        lid = get_id("Lead")
        fn, ln = random.choice(first_names), random.choice(last_names)
        prod = random.choice(products)
        pid, bid, mid = prod[0], prod[1], prod[2]
        
        # All fields filled
        cur.execute("""
            INSERT INTO leads (
                id, first_name, last_name, email, phone, status, 
                brand_id, model_id, product_id, is_converted, is_followed, 
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lid, fn, ln, f"{fn.lower()}.{ln.lower()}{random.randint(100,999)}@rich-test.com",
            f"010-{random.randint(1000,9999)}-{random.randint(1000,9999)}",
            random.choice(["New", "Follow Up", "Qualified"]),
            bid, mid, pid, 0, 0,
            now - timedelta(days=random.randint(0, 3)), # Very recent
            now
        ))

    # 2. Generate 10 Rich Opportunities (Recent)
    for i in range(10):
        oid = get_id("Opp")
        aid = random.choice(account_ids)
        prod = random.choice(products)
        pid, bid, mid = prod[0], prod[1], prod[2]
        
        # All fields filled
        cur.execute("""
            INSERT INTO opportunities (
                id, account_id, product_id, brand_id, model_id, 
                name, amount, stage, temperature, status, is_followed, 
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            oid, aid, pid, bid, mid,
            f"Super Deal {i+1}",
            random.randint(80000000, 300000000),
            random.choice(stages),
            random.choice(["Hot", "Warm", "Cold"]),
            "Open", 0,
            now - timedelta(days=random.randint(0, 3)), # Within "This weekend" range (last 7 days)
            now
        ))

    conn.commit()
    conn.close()
    print("Rich test data generation complete.")

if __name__ == "__main__":
    generate_rich_test_data()
