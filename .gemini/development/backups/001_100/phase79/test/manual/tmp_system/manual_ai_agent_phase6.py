import asyncio
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_ROOT = Path(__file__).resolve().parents[3]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from test.manual._runtime import bootstrap_runtime, should_reset_database

engine, TestingSessionLocal, Base = bootstrap_runtime()
from ai_agent.backend.service import AiAgentService
from db.models import Product, Asset

async def test_phase6():
    if should_reset_database():
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing GREETING ---")
        greet_res = await AiAgentService.process_query(db, "Hi! Who are you?")
        print(f"Intent: {greet_res.get('intent')}")
        print(f"Text: {greet_res.get('text')}")

        print("\n--- Testing UNKNOWN QUESTION ---")
        unknown_res = await AiAgentService.process_query(db, "What is the best car in the world?")
        print(f"Intent: {unknown_res.get('intent')}")
        print(f"Text: {unknown_res.get('text')}")

        print("\n--- Testing PRODUCT CREATE ---")
        prod_res = await AiAgentService.process_query(db, "Create a product named 'Turbo Charger' with category 'Engine' and price 500000")
        print(f"Intent: {prod_res.get('intent')}")
        print(f"Text: {prod_res.get('text')}")
        turbo = db.query(Product).filter(Product.name == "Turbo Charger").first()
        if turbo: print(f"Verified Product in DB: {turbo.id}")

        print("\n--- Testing ASSET CREATE ---")
        asset_res = await AiAgentService.process_query(db, "Create an asset 'John's BMW' with vin 'BMW123456789'")
        print(f"Intent: {asset_res.get('intent')}")
        print(f"Text: {asset_res.get('text')}")
        bmw = db.query(Asset).filter(Asset.vin == "BMW123456789").first()
        if bmw: print(f"Verified Asset in DB: {bmw.id}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_phase6())
