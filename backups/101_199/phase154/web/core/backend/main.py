import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse

# Core Backend Imports
from web.core.backend.api.api_router import api_router
from web.core.backend.core.templates import templates
from web.core.backend.core.toggles import FEATURE_TOGGLES

from db.database import engine, Base
from db import models
import logging

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="AI Ready CRM (Modular)", lifespan=lifespan)

logger = logging.getLogger(__name__)

# Set global feature toggles in templates
templates.env.globals["FEATURE_TOGGLES"] = FEATURE_TOGGLES

# BASE_DIR is .gemini/development/web/
BASE_DIR = Path(__file__).resolve().parents[3]

# Mount Core Static Files
CORE_STATIC = BASE_DIR / "core" / "frontend" / "static"
UPLOADS_STATIC = BASE_DIR / "app" / "static" / "uploads"

if UPLOADS_STATIC.exists():
    app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_STATIC)), name="static_uploads")

if CORE_STATIC.exists():
    app.mount("/static", StaticFiles(directory=str(CORE_STATIC)), name="static")

# Mount AI Agent Sub-app
try:
    from ai_agent.backend.main import app as ai_agent_app
    app.mount("/ai-agent", ai_agent_app)
    logger.info("AI Agent sub-app mounted at /ai-agent")
except ImportError as e:
    logger.error(f"Failed to import AI Agent sub-app: {e}")

# Exception Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception: {exc}")
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})
    referer = request.headers.get("referer", "/leads")
    sep = "&" if "?" in referer else "?"
    return RedirectResponse(url=f"{referer}{sep}error={str(exc).replace(' ', '+')}", status_code=303)

@app.exception_handler(404)
async def custom_404_handler(request: Request, __):
    return HTMLResponse(content="<h1>404 Not Found</h1>", status_code=404)

from fastapi.exceptions import RequestValidationError
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msg = "; ".join([f"{' -> '.join([str(l) for l in e.get('loc', [])])}: {e.get('msg')}" for e in exc.errors()])
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(status_code=422, content={"status": "error", "message": error_msg})
    referer = request.headers.get("referer", "/")
    sep = "&" if "?" in referer else "?"
    return RedirectResponse(url=f"{referer}{sep}error={error_msg.replace(' ', '+')}", status_code=303)

# Include Modular API Routers
app.include_router(api_router)
