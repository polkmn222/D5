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
from ask_agent.ask_agent_service import AskAgentService
from db.models import Opportunity

# Use a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent_opp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_opportunity_crud():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing Opportunity QUERY ---")
        # Add a dummy opp first
        dummy = Opportunity(id="TESTOPP001", name="Test Deal", amount=50000000, stage="Prospecting")
        db.add(dummy)
        db.commit()
        
        response = await AskAgentService.process_query(db, "Show me opportunities with amount greater than 10,000,000")
        print(f"Intent: {response.get('intent')}")
        print(f"Text: {response.get('text')}")
        print(f"SQL: {response.get('sql')}")
        print(f"Results Count: {len(response.get('results', []))}")
        
        if response.get('results'):
            print(f"First Result: {response['results'][0].get('name')} - {response['results'][0].get('amount')}")

        print("\n--- Testing Opportunity CREATE ---")
        create_response = await AskAgentService.process_query(db, "Create a new opportunity for Big Sale with amount 100,000,000")
        print(f"Intent: {create_response.get('intent')}")
        print(f"Text: {create_response.get('text')}")
        
        # Verify in DB
        big_sale = db.query(Opportunity).filter(Opportunity.name == "Big Sale").first()
        if big_sale:
            print(f"Successfully verified Big Sale in DB with ID: {big_sale.id}")
            
            print("\n--- Testing Opportunity UPDATE ---")
            update_response = await AskAgentService.process_query(db, f"Change Big Sale ({big_sale.id}) stage to Closed Won")
            print(f"Intent: {update_response.get('intent')}")
            print(f"Text: {update_response.get('text')}")
            
            db.refresh(big_sale)
            print(f"Verified Updated Stage: {big_sale.stage}")
        else:
            print("Failed to find Big Sale in DB.")

    finally:
        db.close()
        # Clean up
        if os.path.exists("./test_ai_agent_opp.db"):
            os.remove("./test_ai_agent_opp.db")

if __name__ == "__main__":
    asyncio.run(test_opportunity_crud())
