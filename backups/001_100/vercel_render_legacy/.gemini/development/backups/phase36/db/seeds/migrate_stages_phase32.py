from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.models import Opportunity
from backend.app.core.enums import OpportunityStage

DATABASE_URL = "sqlite:///./crm.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
