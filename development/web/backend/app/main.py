import os
from pathlib import Path
from contextlib import asynccontextmanager
import time
import logging

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse

# Relocated Imports back to original paths
from web.backend.app.api.api_router import api_router
from web.backend.app.core.templates import templates
from web.backend.app.core.toggles import FEATURE_TOGGLES
from web.backend.app.utils.perf_diagnostics import RequestTimingMiddleware, diagnostics_enabled

from db.database import engine, Base
from db import models

@asynccontextmanager
async def lifespan(_: FastAPI):
    startup_started_at = time.perf_counter()
    Base.metadata.create_all(bind=engine)
    if diagnostics_enabled():
        logger.info(
            "web_perf_startup component=lifespan_create_all duration_ms=%.2f",
            (time.perf_counter() - startup_started_at) * 1000,
        )
    yield

app = FastAPI(title="AI Ready CRM", lifespan=lifespan)
app.add_middleware(RequestTimingMiddleware)

logger = logging.getLogger(__name__)

# Set global feature toggles in templates
templates.env.globals["FEATURE_TOGGLES"] = FEATURE_TOGGLES

# Determine base directory for web
# This file is at development/web/backend/app/main.py
CURRENT_FILE = Path(__file__).resolve()
WEB_ROOT = CURRENT_FILE.parents[2] # development/web/

# Mount Static Files with verified absolute paths
UPLOADS_DIR = WEB_ROOT / "app" / "static" / "uploads"
STATIC_DIR = WEB_ROOT / "frontend" / "static"

app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="static_uploads")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount AI Agent Sub-app
try:
    from ai_agent.ui.backend.main import app as ai_agent_app
    app.mount("/ai-agent", ai_agent_app)
    logger.info("AI Agent sub-app mounted at /ai-agent")
except ImportError as e:
    logger.error(f"Failed to import AI Agent sub-app: {e}")

try:
    from agent.ui.backend.main import app as ops_agent_app
    app.mount("/agent", ops_agent_app)
    logger.info("Ops Pilot sub-app mounted at /agent")
except ImportError as e:
    logger.error(f"Failed to import Ops Pilot sub-app: {e}")

# Mount Agent Gem Sub-app
try:
    from agent_gem.backend.main import app as agent_gem_app
    app.mount("/agent-gem", agent_gem_app)
    logger.info("Agent Gem sub-app mounted at /agent-gem")
except ImportError as e:
    logger.error(f"Failed to import Agent Gem sub-app: {e}")

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

# Include API Router
app.include_router(api_router)
