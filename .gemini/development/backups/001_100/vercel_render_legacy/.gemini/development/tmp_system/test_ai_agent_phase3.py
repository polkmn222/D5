import asyncio
import os
import sys
import logging
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), ".gemini", "skills"))

from db.database import Base
from backend.app.services.ask_agent.ask_agent_service import AskAgentService
from db.models import Contact

# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent_contact.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_contact_crud():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing Contact QUERY ---")
        # Add a dummy contact first
        dummy = Contact(id="TESTCON001", first_name="Bruce", last_name="Wayne", email="bruce@waynecorp.com")
        db.add(dummy)
        db.commit()
        
        response = await AskAgentService.process_query(db, "Show me contacts named Wayne")
        print(f"Intent: {response.get('intent')}")
        print(f"Text: {response.get('text')}")
        print(f"SQL: {response.get('sql')}")
        print(f"Results Count: {len(response.get('results', []))}")
        
        if response.get('results'):
            print(f"First Result: {response['results'][0].get('first_name')} {response['results'][0].get('last_name')}")

        print("\n--- Testing Contact CREATE ---")
        create_response = await AskAgentService.process_query(db, "Create a contact for Tony Stark with email tony@stark.com")
        print(f"Intent: {create_response.get('intent')}")
        print(f"Text: {create_response.get('text')}")
        
        # Verify in DB
        tony = db.query(Contact).filter(Contact.last_name == "Stark").first()
        if tony:
            print(f"Successfully verified Tony Stark in DB with ID: {tony.id}")
            
            print("\n--- Testing Contact UPDATE ---")
            update_response = await AskAgentService.process_query(db, f"Change Tony Stark's ({tony.id}) email to ironman@avengers.com")
            print(f"Intent: {update_response.get('intent')}")
            print(f"Text: {update_response.get('text')}")
            
            db.refresh(tony)
            print(f"Verified Updated Email: {tony.email}")
        else:
            print("Failed to find Tony Stark in DB.")

    finally:
        db.close()
        # Clean up
        if os.path.exists("./test_ai_agent_contact.db"):
            os.remove("./test_ai_agent_contact.db")

if __name__ == "__main__":
    asyncio.run(test_contact_crud())
