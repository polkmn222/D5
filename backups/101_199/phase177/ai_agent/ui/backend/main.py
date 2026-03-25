from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

# Create the sub-app
app = FastAPI(title="AI Agent Sub-app", version="1.0.0")

# Determine base directory for AI Agent
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

# Mount static files within the sub-app
# If sub-app is mounted at /ai-agent in main app, 
# then /ai-agent/static will serve these files.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="ai_agent_static")

# Import and include the local router
from ai_agent.ui.backend.router import router as chat_router
app.include_router(chat_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "module": "ai_agent"}
