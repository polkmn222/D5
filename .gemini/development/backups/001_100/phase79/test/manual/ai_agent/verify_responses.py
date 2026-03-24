import asyncio
import sys
import json
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[3]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from test.manual._runtime import bootstrap_runtime, should_reset_database

engine, SessionLocal, Base = bootstrap_runtime()
from ai_agent.backend.service import AiAgentService

async def verify_command(query):
    db = SessionLocal()
    print(f"\n>>> USER COMMAND: \"{query}\"")
    
    try:
        response = await AiAgentService.process_query(db, query)
        print(f"--- PROCESSED RESPONSE ---")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"ERROR: {str(e)}")
    finally:
        db.close()

async def run_verification():
    if should_reset_database():
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    commands = [
        "current created lead",
        "Show me all leads",
        "Create a contact named John Doe with email john@doe.com",
        "Find contacts with email john@doe.com"
    ]
    for cmd in commands:
        await verify_command(cmd)

if __name__ == "__main__":
    asyncio.run(run_verification())
