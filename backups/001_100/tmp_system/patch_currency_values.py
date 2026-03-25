import sqlite3

db_path = "/Users/sangyeol.park@gruve.ai/D4/crm.db"

def patch_currency_values():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    print("Patching Opportunity amounts (rounding to nearest 1,000)...")
    cur.execute("SELECT id, amount FROM opportunities")
    opps = cur.fetchall()
    for oid, amt in opps:
        if amt:
            new_amt = (amt // 1000) * 1000
            cur.execute("UPDATE opportunities SET amount = ? WHERE id = ?", (new_amt, oid))
            
    print("Patching Asset prices (rounding to nearest 1,000)...")
    cur.execute("SELECT id, price FROM assets")
    assets = cur.fetchall()
    for aid, price in assets:
        if price:
            new_price = (price // 1000) * 1000
            cur.execute("UPDATE assets SET price = ? WHERE id = ?", (new_price, aid))
            
    conn.commit()
    conn.close()
    print("Currency value patching complete.")

if __name__ == "__main__":
    patch_currency_values()
