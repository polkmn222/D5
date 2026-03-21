import os
import sys

from sqlalchemy import inspect, text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db.database import engine

def migrate():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    try:
        if "messages" not in tables:
            print("Old 'messages' table not found. No migration needed.")
            return

        if "message_sends" not in tables:
            print("New 'message_sends' table not found. Please run the app first to create it.")
            return

        print("Migrating records from 'messages' to 'message_sends'...")

        migrated_count = 0

        with engine.begin() as connection:
            rows = connection.execute(text("SELECT * FROM messages")).mappings().all()

            for record in rows:
                existing = connection.execute(
                    text("SELECT id FROM message_sends WHERE id = :id"),
                    {"id": record["id"]},
                ).first()

                if existing:
                    continue

                connection.execute(
                    text(
                        """
                        INSERT INTO message_sends (
                            id,
                            contact,
                            template,
                            direction,
                            content,
                            status,
                            sent_at,
                            created_at,
                            updated_at,
                            deleted_at
                        ) VALUES (
                            :id,
                            :contact,
                            :template,
                            :direction,
                            :content,
                            :status,
                            :sent_at,
                            :created_at,
                            :updated_at,
                            :deleted_at
                        )
                        """
                    ),
                    {
                        "id": record["id"],
                        "contact": record.get("contact"),
                        "template": record.get("template"),
                        "direction": record.get("direction"),
                        "content": record.get("content"),
                        "status": record.get("status"),
                        "sent_at": record.get("created_at"),
                        "created_at": record.get("created_at"),
                        "updated_at": record.get("updated_at"),
                        "deleted_at": record.get("deleted_at"),
                    },
                )
                migrated_count += 1

        print(f"Successfully migrated {migrated_count} records.")

    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == "__main__":
    migrate()
