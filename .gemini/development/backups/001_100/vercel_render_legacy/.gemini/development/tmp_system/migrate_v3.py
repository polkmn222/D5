import sqlite3
import os

DB_PATH = "crm.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Disable foreign key checks for migration
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Helper to check if column exists
        def column_exists(table, column):
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [info[1] for info in cursor.fetchall()]
            return column in columns

        def rename_safe(table, old_col, new_col):
            if column_exists(table, old_col):
                if column_exists(table, new_col):
                    print(f"Dropping redundant column {new_col} in {table} before renaming.")
                    # SQLite doesn't support DROP COLUMN directly in older versions, 
                    # but 3.35.0+ does. Let's try simple ALTER TABLE DROP COLUMN.
                    # If it fails, we might need a full table recreate.
                    try:
                        cursor.execute(f"ALTER TABLE {table} DROP COLUMN {new_col};")
                    except sqlite3.OperationalError:
                        print(f"ALTER TABLE DROP COLUMN failed for {table}.{new_col}. Recreating table might be needed.")
                        raise
                cursor.execute(f"ALTER TABLE {table} RENAME COLUMN {old_col} TO {new_col};")
                print(f"Renamed {table}.{old_col} to {new_col}")

        # 1. vehicle_specifications: parent_id -> parent (already done in some cases)
        rename_safe("vehicle_specifications", "parent_id", "parent")

        # 2. models: brand_id -> brand (already done in some cases)
        rename_safe("models", "brand_id", "brand")

        # 3. contacts: account_id -> account (already done in some cases)
        rename_safe("contacts", "account_id", "account")

        # 4. leads: rename multiple (already done in some cases)
        rename_safe("leads", "converted_account_id", "converted_account")
        rename_safe("leads", "converted_opportunity_id", "converted_opportunity")
        rename_safe("leads", "campaign_id", "campaign")
        rename_safe("leads", "brand_id", "brand")
        rename_safe("leads", "model_id", "model")
        rename_safe("leads", "product_id", "product")

        # 5. products: brand_id -> brand, model_id -> model
        rename_safe("products", "brand_id", "brand")
        rename_safe("products", "model_id", "model")

        # 6. opportunities: rename multiple
        rename_safe("opportunities", "account_id", "account")
        rename_safe("opportunities", "product_id", "product")
        rename_safe("opportunities", "lead_id", "lead")
        rename_safe("opportunities", "brand_id", "brand")
        rename_safe("opportunities", "model_id", "model")
        rename_safe("opportunities", "asset_id", "asset")

        # 7. assets: rename multiple
        rename_safe("assets", "account_id", "account")
        rename_safe("assets", "product_id", "product")
        rename_safe("assets", "brand_id", "brand")
        rename_safe("assets", "model_id", "model")

        # 8. tasks: account_id -> account, opportunity_id -> opportunity, message_id -> message
        rename_safe("tasks", "account_id", "account")
        rename_safe("tasks", "opportunity_id", "opportunity")
        rename_safe("tasks", "message_id", "message")

        # 9. messages: contact_id -> contact, account_id -> account, template_id -> template
        rename_safe("messages", "contact_id", "contact")
        rename_safe("messages", "account_id", "account")
        rename_safe("messages", "template_id", "template")

        # Commit changes
        conn.commit()
        print("Migration successful.")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.close()

if __name__ == "__main__":
    migrate()
