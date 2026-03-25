import asyncio
import os
import sys
import logging
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), ".gemini", "skills"))

from db.database import Base
from ask_agent.ask_agent_service import AskAgentService
from db.models import Product, Asset

# Use a test database
TEST_DB_PATH = Path(__file__).resolve().parents[2] / "databases" / "legacy" / "test_ai_agent_phase6.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_phase6():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing GREETING ---")
        greet_res = await AskAgentService.process_query(db, "Hi! Who are you?")
        print(f"Intent: {greet_res.get('intent')}")
        print(f"Text: {greet_res.get('text')}")

        print("\n--- Testing UNKNOWN QUESTION ---")
        unknown_res = await AskAgentService.process_query(db, "What is the best car in the world?")
        print(f"Intent: {unknown_res.get('intent')}")
        print(f"Text: {unknown_res.get('text')}")

        print("\n--- Testing PRODUCT CREATE ---")
        prod_res = await AskAgentService.process_query(db, "Create a product named 'Turbo Charger' with category 'Engine' and price 500000")
        print(f"Intent: {prod_res.get('intent')}")
        print(f"Text: {prod_res.get('text')}")
        turbo = db.query(Product).filter(Product.name == "Turbo Charger").first()
        if turbo: print(f"Verified Product in DB: {turbo.id}")

        print("\n--- Testing ASSET CREATE ---")
        asset_res = await AskAgentService.process_query(db, "Create an asset 'John's BMW' with vin 'BMW123456789'")
        print(f"Intent: {asset_res.get('intent')}")
        print(f"Text: {asset_res.get('text')}")
        bmw = db.query(Asset).filter(Asset.vin == "BMW123456789").first()
        if bmw: print(f"Verified Asset in DB: {bmw.id}")

    finally:
        db.close()
        # Clean up
        if os.path.exists("./test/databases/legacy/test_ai_agent_phase6.db"):
            os.remove("./test/databases/legacy/test_ai_agent_phase6.db")

if __name__ == "__main__":
    asyncio.run(test_phase6())
