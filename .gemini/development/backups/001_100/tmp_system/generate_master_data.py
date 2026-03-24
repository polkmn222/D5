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
    # Mocking KST as UTC+9
    return datetime.utcnow() + timedelta(hours=9)

def generate_master_data():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("Populating master data...")
    now = get_kst_now()

    # 1. Brands (Vehicle Specs)
    brands = [
        "Solaris", "Luna Motors", "Terra Motors", "Astra", "Nova", 
        "Zenith", "Apex", "Equinox", "Valiant", "Hyperion"
    ]
    brand_ids = []
    for b in brands:
        bid = get_id("Brand")
        cur.execute("INSERT INTO vehicle_specifications (id, name, record_type, created_at, updated_at) VALUES (?, ?, ?, ?, ?)", 
                    (bid, b, "Brand", now, now))
        brand_ids.append(bid)
    
    # 2. Models
    models_pool = [
        "Model S", "Model 3", "Model X", "Model Y", "Taycan", "911 Carrera", "Ioniq 5", "Bolt EV", "Leaf Plus",
        "CyberTruck", "Rivian R1T", "Lucid Air", "Polestar 2", "V60", "XC90", "EV6", "GV70", "Series 5", "A6", "E-Class"
    ]
    model_ids = []
    for m in models_pool:
        mid = get_id("Model")
        bid = random.choice(brand_ids)
        cur.execute("INSERT INTO models (id, name, brand_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)", 
                    (mid, m, bid, now, now))
        model_ids.append(mid)
        
    # 3. Products
    product_ids = []
    for i in range(30):
        pid = get_id("Product")
        mid = random.choice(model_ids)
        cur.execute("SELECT brand_id FROM models WHERE id = ?", (mid,))
        bid = cur.fetchone()[0]
        cur.execute("INSERT INTO products (id, name, brand_id, model_id, base_price, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                    (pid, f"Premium Build {i+1}", bid, mid, random.randint(40000000, 200000000), "Vehicle", now, now))
        product_ids.append(pid)

    # 4. Campaigns
    campaign_ids = []
    camp_names = ["Spring Sales Expo", "EV Transition Drive", "Summer Luxury Promo", "Autumn Fleet Clearance", "Winter Safety Week"]
    for cn in camp_names:
        cid = get_id("Camp")
        cur.execute("INSERT INTO campaigns (id, name, type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (cid, cn, "Webinar", "Active", now, now))
        campaign_ids.append(cid)
        
    # 5. Accounts
    account_ids = []
    acc_names = [
        "Stark Enterprises", "Wayne Corp", "LexCorp", "Oscorp", "Pym Tech", 
        "Globex", "Initech", "Umbrella Corp", "Cyberdyne", "Weyland-Yutani",
        "Nakatomi", "Hooli", "Pied Piper", "Dunder Mifflin", "Vandelay Industries",
        "Aperture Science", "Black Mesa", "Prestige Worldwide", "Talon", "Gruve AI"
    ]
    for i in range(40):
        aid = get_id("Account")
        name = random.choice(acc_names) + f" {random.randint(100, 999)}"
        cur.execute("INSERT INTO accounts (id, name, record_type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", 
                    (aid, name, random.choice(["Individual", "Corporate"]), "Active", now, now))
        account_ids.append(aid)
        
    # 6. Contacts
    contact_ids = []
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    for i in range(40):
        cid = get_id("Contact")
        aid = random.choice(account_ids)
        fn, ln = random.choice(first_names), random.choice(last_names)
        cur.execute("INSERT INTO contacts (id, account_id, first_name, last_name, email, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                    (cid, aid, fn, ln, f"{fn.lower()}.{ln.lower()}{i}@example.com", now, now))
        contact_ids.append(cid)
        
        # 7. Leads
    lead_ids = []
    for i in range(50):
        lid = get_id("Lead")
        fn, ln = random.choice(first_names), random.choice(last_names)
        cur.execute("INSERT INTO leads (id, first_name, last_name, status, is_converted, is_followed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                    (lid, fn, ln, random.choice(["New", "Follow Up", "Qualified"]), 0, 0, now - timedelta(days=random.randint(0, 700)), now))
        lead_ids.append(lid)
        
    # 8. Opportunities
    opportunity_ids = []
    stages = ["Qualification", "Test Drive", "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost"]
    for i in range(50):
        oid = get_id("Opp")
        aid = random.choice(account_ids)
        pid = random.choice(product_ids)
        cur.execute("SELECT brand_id, model_id FROM products WHERE id = ?", (pid,))
        row = cur.fetchone()
        bid, mid = row[0], row[1]
        cur.execute("INSERT INTO opportunities (id, account_id, product_id, brand_id, model_id, name, amount, stage, temperature, status, is_followed, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (oid, aid, pid, bid, mid, f"Strategic Deal {i+1}", random.randint(60000000, 250000000), random.choice(stages), random.choice(["Hot", "Warm", "Cold"]), "Open", 0, now - timedelta(days=random.randint(0, 700)), now))
        opportunity_ids.append(oid)
        
    # 9. Assets
    for i in range(40):
        asid = get_id("Asset")
        aid = random.choice(account_ids)
        pid = random.choice(product_ids)
        cur.execute("SELECT brand_id, model_id FROM products WHERE id = ?", (pid,))
        row = cur.fetchone()
        bid, mid = row[0], row[1]
        cur.execute("INSERT INTO assets (id, account_id, product_id, brand_id, model_id, name, status, price, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (asid, aid, pid, bid, mid, f"Delivered Asset {i+1}", "Active", random.randint(50000000, 190000000), now, now))
                    
    # 10. Message Templates
    template_ids = []
    templates_data = [
        ("Premium Welcome", "Welcome to Solaris Luxury", "Hi {name}, we are thrilled to have you here."),
        ("Test Drive Invite", "Your Test Drive Awaits", "Hi {name}, your Taycan is ready for a spin."),
        ("Post-Sale Follow-up", "How is your new Solaris?", "Hi {name}, we hope you're loving the journey."),
        ("Maintenance Reminder", "Time for a pit stop", "Hi {name}, your vehicle service is due.")
    ]
    for name, sub, body in templates_data:
        tid = get_id("Template")
        cur.execute("INSERT INTO message_templates (id, name, subject, body, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)", 
                    (tid, name, sub, body, now, now))
        template_ids.append(tid)
        
    # 11. Messages
    message_ids = []
    for i in range(50):
        msid = get_id("Message")
        cid = random.choice(contact_ids)
        tid = random.choice(template_ids)
        cur.execute("INSERT INTO messages (id, contact_id, template_id, content, direction, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (msid, cid, tid, f"System Message notification {i+1}", "Outbound", "Sent", now, now))
        message_ids.append(msid)
        
    conn.commit()
    conn.close()
    print("Master data generation complete.")

if __name__ == "__main__":
    generate_master_data()
