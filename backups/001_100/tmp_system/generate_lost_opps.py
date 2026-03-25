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

def generate_lost_opps():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("Generating 2 'Closed Lost' Opportunities for chart visibility...")
    now = get_kst_now()

    # Get available Account, Product
    cur.execute("SELECT id FROM accounts LIMIT 5")
    account_ids = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT id, brand_id, model_id FROM products LIMIT 5")
    products = cur.fetchall()

    for i in range(2):
        oid = get_id("Opp")
        aid = random.choice(account_ids)
        prod = random.choice(products)
        pid, bid, mid = prod[0], prod[1], prod[2]
        
        cur.execute("""
            INSERT INTO opportunities (
                id, account_id, product_id, brand_id, model_id, 
                name, amount, stage, temperature, status, is_followed, 
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            oid, aid, pid, bid, mid,
            f"Lost Hope {i+1}",
            random.randint(50000000, 150000000),
            "Closed Lost",
            "Cold",
            "Closed", 0,
            now - timedelta(days=random.randint(0, 3)),
            now
        ))

    conn.commit()
    conn.close()
    print("Lost test data generation complete.")

if __name__ == "__main__":
    generate_lost_opps()
