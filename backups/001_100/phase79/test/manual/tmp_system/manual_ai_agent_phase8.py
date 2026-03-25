import asyncio
import sys
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_ROOT = Path(__file__).resolve().parents[3]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from test.manual._runtime import bootstrap_runtime, should_reset_database

engine, TestingSessionLocal, Base = bootstrap_runtime()
from ai_agent.backend.service import AiAgentService

async def test_phase8_messaging():
    if should_reset_database():
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        # Mocking MessagingService to avoid external delivery calls
        with patch("web.backend.app.services.messaging_service.MessagingService.bulk_send") as mock_bulk:
            mock_bulk.return_value = 2
            
            print("\n--- Testing BULK MESSAGE ---")
            msg_res = await AiAgentService.process_query(db, "Send the Welcome template to contacts 003abc and 003def")
            print(f"Intent: {msg_res.get('intent')}")
            print(f"Text: {msg_res.get('text')}")
            print(f"Data: {msg_res.get('data')}")
            
            mock_bulk.assert_called_once()
            args, kwargs = mock_bulk.call_args
            print(f"Mock called with contact_ids: {kwargs.get('contact_ids')}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_phase8_messaging())
