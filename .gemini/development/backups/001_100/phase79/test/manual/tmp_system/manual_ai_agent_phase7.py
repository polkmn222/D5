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
from db.models import MessageTemplate, MessageSend

async def test_phase7_crud():
    if should_reset_database():
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        print("\n--- Testing TEMPLATE CREATE ---")
        temp_res = await AiAgentService.process_query(db, "Create an LMS template named 'Holiday' with subject 'Happy Holidays' and content 'Wish you a great year!'")
        print(f"Intent: {temp_res.get('intent')}")
        print(f"Text: {temp_res.get('text')}")
        holiday = db.query(MessageTemplate).filter(MessageTemplate.name == "Holiday").first()
        if holiday: print(f"Verified Template in DB: {holiday.id} ({holiday.record_type})")

        print("\n--- Testing MESSAGE LOG CREATE ---")
        msg_res = await AiAgentService.process_query(db, "Log an outbound message for contact 003_test with content 'Test message' and status 'Sent'")
        print(f"Intent: {msg_res.get('intent')}")
        print(f"Text: {msg_res.get('text')}")
        msg = db.query(MessageSend).filter(MessageSend.content == "Test message").first()
        if msg: print(f"Verified Message Log in DB: {msg.id}")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_phase7_crud())
