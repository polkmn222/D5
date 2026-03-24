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
from db.models import Contact

async def test_contact_crud():
    if should_reset_database():
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing Contact QUERY ---")
        # Add a dummy contact first
        dummy = Contact(id="TESTCON001", first_name="Bruce", last_name="Wayne", email="bruce@waynecorp.com")
        db.add(dummy)
        db.commit()
        
        response = await AiAgentService.process_query(db, "Show me contacts named Wayne")
        print(f"Intent: {response.get('intent')}")
        print(f"Text: {response.get('text')}")
        print(f"SQL: {response.get('sql')}")
        print(f"Results Count: {len(response.get('results', []))}")
        
        if response.get('results'):
            print(f"First Result: {response['results'][0].get('first_name')} {response['results'][0].get('last_name')}")

        print("\n--- Testing Contact CREATE ---")
        create_response = await AiAgentService.process_query(db, "Create a contact for Tony Stark with email tony@stark.com")
        print(f"Intent: {create_response.get('intent')}")
        print(f"Text: {create_response.get('text')}")
        
        # Verify in DB
        tony = db.query(Contact).filter(Contact.last_name == "Stark").first()
        if tony:
            print(f"Successfully verified Tony Stark in DB with ID: {tony.id}")
            
            print("\n--- Testing Contact UPDATE ---")
            update_response = await AiAgentService.process_query(db, f"Change Tony Stark's ({tony.id}) email to ironman@avengers.com")
            print(f"Intent: {update_response.get('intent')}")
            print(f"Text: {update_response.get('text')}")
            
            db.refresh(tony)
            print(f"Verified Updated Email: {tony.email}")
        else:
            print("Failed to find Tony Stark in DB.")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_contact_crud())
