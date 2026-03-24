import sqlite3

def migrate():
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()

    # Create models table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS models (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        brand_id TEXT,
        description TEXT,
        created_at DATETIME,
        updated_at DATETIME,
        deleted_at DATETIME,
        FOREIGN KEY(brand_id) REFERENCES vehicle_specifications(id)
    )
    ''')

    # Add columns to existing tables
    tables_to_update = ['leads', 'opportunities', 'assets']
    for table in tables_to_update:
        try:
            cursor.execute(f'ALTER TABLE {table} ADD COLUMN model_id TEXT')
            print(f"Added model_id to {table}")
        except sqlite3.OperationalError as e:
            print(f"Skipping {table}: {e}")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
