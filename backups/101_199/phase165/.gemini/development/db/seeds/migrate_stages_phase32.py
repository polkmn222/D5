import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db.database import SessionLocal
from db.models import Opportunity

def migrate():
    db = SessionLocal()
    try:
        # Update Opportunity stages
        updated = db.query(Opportunity).filter(Opportunity.stage == "Needs Analysis").update({"stage": "Test drive"}, synchronize_session=False)
        db.commit()
        print(f"Successfully migrated {updated} Opportunity records.")
    except Exception as e:
        db.rollback()
        print(f"Migration error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
