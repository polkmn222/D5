import sqlite3
import os
import uuid
from datetime import datetime

def migrate():
    db_path = "app/crm.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if old messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not cursor.fetchone():
            print("Old 'messages' table not found. No migration needed.")
            return

        # Check if new message_sends table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='message_sends'")
        if not cursor.fetchone():
            print("New 'message_sends' table not found. Please run the app first to create it.")
            return

        print("Migrating records from 'messages' to 'message_sends'...")
        
        # Fetch records from old table
        # Old schema likely: id, contact, template, direction, content, status, created_at, updated_at, deleted_at
        cursor.execute("SELECT * FROM messages")
        rows = cursor.fetchall()
        
        # Get column names for better mapping
        cursor.execute("PRAGMA table_info(messages)")
        old_cols = [c[1] for c in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(message_sends)")
        new_cols = [c[1] for c in cursor.fetchall()]
        
        migrated_count = 0
        for row in rows:
            record = dict(zip(old_cols, row))
            
            # Check if record already exists in message_sends
            cursor.execute("SELECT id FROM message_sends WHERE id = ?", (record['id'],))
            if cursor.fetchone():
                continue
                
            # Insert into new table
            # New schema fields: id, contact, template, direction, content, status, provider_message_id, sent_at, created_at, updated_at, deleted_at
            cursor.execute("""
                INSERT INTO message_sends (id, contact, template, direction, content, status, sent_at, created_at, updated_at, deleted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record['id'],
                record.get('contact'),
                record.get('template'),
                record.get('direction'),
                record.get('content'),
                record.get('status'),
                record.get('created_at'), # sent_at
                record.get('created_at'),
                record.get('updated_at'),
                record.get('deleted_at')
            ))
            migrated_count += 1
            
        conn.commit()
        print(f"Successfully migrated {migrated_count} records.")
        
        # Optionally rename old table instead of deleting
        # cursor.execute("ALTER TABLE messages RENAME TO messages_old")
        # conn.commit()
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
