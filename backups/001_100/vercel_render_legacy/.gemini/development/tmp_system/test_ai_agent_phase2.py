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
from db.models import Lead

# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_lead_crud():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing Lead QUERY ---")
        # Add a dummy lead first
        dummy = Lead(id="TESTLEAD001", first_name="Test", last_name="User", email="test@example.com")
        db.add(dummy)
        db.commit()
        
        response = await AskAgentService.process_query(db, "Show me some of the recently created leads")
        print(f"Intent: {response.get('intent')}")
        print(f"Text: {response.get('text')}")
        print(f"SQL: {response.get('sql')}")
        print(f"Results Count: {len(response.get('results', []))}")
        
        if response.get('results'):
            print(f"First Result Name: {response['results'][0].get('first_name')} {response['results'][0].get('last_name')}")

        print("\n--- Testing Lead CREATE ---")
        create_response = await AskAgentService.process_query(db, "Create a new lead for John Wick with phone 010-1234-5678")
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
        # Clean up
        if os.path.exists("./test_ai_agent.db"):
            os.remove("./test_ai_agent.db")

if __name__ == "__main__":
    asyncio.run(test_lead_crud())
