import asyncio
import os
import sys
import json
from dotenv import load_dotenv

# Add project root and .gemini/skills to path
ROOT_DIR = os.getcwd()
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, ".gemini", "skills"))

from ai_agent.backend.service import AiAgentService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv(os.path.join(ROOT_DIR, ".gemini", "skills", ".env"))

# Setup DB (Memory for verification)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize Schema
from db.database import Base
Base.metadata.create_all(bind=engine)

async def verify_command(query):
    db = SessionLocal()
    print(f"\n>>> USER COMMAND: \"{query}\"")
    
    # Capture the raw LLM response by wrapping _call_llm
    original_call_llm = AiAgentService._call_llm
    raw_response = [None]
    
    async def wrapped_call_llm(user_query, system_prompt):
        resp = await original_call_llm(user_query, system_prompt)
        raw_response[0] = resp
        return resp
        
    AiAgentService._call_llm = wrapped_call_llm
    
    try:
        response = await AiAgentService.process_query(db, query)
        print(f"--- RAW LLM REPLY ---")
        print(raw_response[0])
        print(f"--- PROCESSED RESPONSE ---")
        print(json.dumps(response, indent=2))
    except Exception as e:
        print(f"ERROR: {str(e)}")
    finally:
        db.close()

async def run_verification():
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
