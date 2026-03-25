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
from db.models import Lead

async def test_lead_crud():
    if should_reset_database():
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing Lead QUERY ---")
        # Add a dummy lead first
        dummy = Lead(id="TESTLEAD001", first_name="Test", last_name="User", email="test@example.com")
        db.add(dummy)
        db.commit()
        
        response = await AiAgentService.process_query(db, "Show me some of the recently created leads")
        print(f"Intent: {response.get('intent')}")
        print(f"Text: {response.get('text')}")
        print(f"SQL: {response.get('sql')}")
        print(f"Results Count: {len(response.get('results', []))}")
        
        if response.get('results'):
            print(f"First Result Name: {response['results'][0].get('first_name')} {response['results'][0].get('last_name')}")

        print("\n--- Testing Lead CREATE ---")
        create_response = await AiAgentService.process_query(db, "Create a new lead for John Wick with phone 010-1234-5678")
        print(f"Intent: {create_response.get('intent')}")
        print(f"Text: {create_response.get('text')}")
        print(f"Data: {create_response.get('data')}")
        
        # Verify in DB
        wick = db.query(Lead).filter(Lead.last_name == "Wick").first()
        if wick:
            print(f"Successfully verified John Wick in DB with ID: {wick.id}")
        else:
            print("Failed to find John Wick in DB.")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_lead_crud())
