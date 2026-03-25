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
from db.models import MessageTemplate, MessageSend

# Use a test database
TEST_DB_PATH = Path(__file__).resolve().parents[2] / "databases" / "legacy" / "test_ai_agent_phase7.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_phase7_crud():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing TEMPLATE CREATE ---")
        temp_res = await AskAgentService.process_query(db, "Create an LMS template named 'Holiday' with subject 'Happy Holidays' and content 'Wish you a great year!'")
        print(f"Intent: {temp_res.get('intent')}")
        print(f"Text: {temp_res.get('text')}")
        holiday = db.query(MessageTemplate).filter(MessageTemplate.name == "Holiday").first()
        if holiday: print(f"Verified Template in DB: {holiday.id} ({holiday.record_type})")

        print("\n--- Testing MESSAGE LOG CREATE ---")
        msg_res = await AskAgentService.process_query(db, f"Log an outbound message for contact 003_test with content 'Test message' and status 'Sent'")
        print(f"Intent: {msg_res.get('intent')}")
        print(f"Text: {msg_res.get('text')}")
        msg = db.query(MessageSend).filter(MessageSend.content == "Test message").first()
        if msg: print(f"Verified Message Log in DB: {msg.id}")

    finally:
        db.close()
        # Clean up
        if os.path.exists("./test/databases/legacy/test_ai_agent_phase7.db"):
            os.remove("./test/databases/legacy/test_ai_agent_phase7.db")

if __name__ == "__main__":
    asyncio.run(test_phase7_crud())
