import asyncio
import os
import sys
import logging
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), ".gemini", "skills"))

from db.database import Base
from ask_agent.ask_agent_service import AskAgentService
from db.models import Contact

# Use a test database
TEST_DB_PATH = Path(__file__).resolve().parents[2] / "databases" / "legacy" / "test_ai_agent_phase8.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def test_phase8_messaging():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        # Mocking MessagingService to avoid actual SUREM calls
        with patch("backend.app.services.messaging_service.MessagingService.bulk_send") as mock_bulk:
            mock_bulk.return_value = 2
            
            print("\n--- Testing BULK MESSAGE ---")
            msg_res = await AskAgentService.process_query(db, "Send the Welcome template to contacts 003abc and 003def")
            print(f"Intent: {msg_res.get('intent')}")
            print(f"Text: {msg_res.get('text')}")
            print(f"Data: {msg_res.get('data')}")
            
            mock_bulk.assert_called_once()
            args, kwargs = mock_bulk.call_args
            print(f"Mock called with contact_ids: {kwargs.get('contact_ids')}")

    finally:
        db.close()
        # Clean up
        if os.path.exists("./test/databases/legacy/test_ai_agent_phase8.db"):
            os.remove("./test/databases/legacy/test_ai_agent_phase8.db")

if __name__ == "__main__":
    asyncio.run(test_phase8_messaging())
