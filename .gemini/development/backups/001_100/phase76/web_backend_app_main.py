import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from web.backend.app.api.api_router import api_router
from db.database import engine, Base
from db import models
import logging

from web.backend.app.core.toggles import FEATURE_TOGGLES


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="AI Ready CRM", lifespan=lifespan)

logger = logging.getLogger(__name__)

# Add context processor for Jinja2 templates
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # This is not a context processor but we can use app.state or similar
    # FastAPI doesn't have a direct context processor like Flask
    # But we can pass it in TemplateResponse
    return await call_next(request)

# Better way: dependency injection or just use it in TemplateResponse
# But to make it available in base.html easily, we can add it to the templates env
from web.backend.app.core.templates import templates
templates.env.globals["FEATURE_TOGGLES"] = FEATURE_TOGGLES

# Mount Main Static Files
BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_STATIC = BASE_DIR / "frontend" / "static"
UPLOADS_STATIC = BASE_DIR / "app" / "static" / "uploads"

if UPLOADS_STATIC.exists():
    app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_STATIC)), name="static_uploads")

app.mount("/static", StaticFiles(directory=str(FRONTEND_STATIC)), name="static")

# Mount AI Agent Sub-app (handles its own /static and /api)
try:
    from ai_agent.backend.main import app as ai_agent_app
    app.mount("/ai-agent", ai_agent_app)
    logger.info("AI Agent sub-app mounted at /ai-agent")
except ImportError as e:
    logger.error(f"Failed to import AI Agent sub-app: {e}")
except Exception as e:
    logger.error(f"Failed to mount AI Agent sub-app: {e}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception: {exc}")
    
    # Check if request expects JSON
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Internal Server Error", "details": str(exc)}
        )

    # For non-JSON requests, redirect back to referer or home with error message
    referer = request.headers.get("referer", "/leads")
    error_msg = str(exc).replace(" ", "+")
    sep = "&" if "?" in referer else "?"
    return RedirectResponse(url=f"{referer}{sep}error={error_msg}", status_code=303)

@app.exception_handler(404)
async def custom_404_handler(request: Request, __):
    return HTMLResponse(content="<h1>404 Not Found</h1><p>The page you are looking for does not exist.</p><a href='/'>Go to Home</a>", status_code=404)

from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    
    # Format errors into a simple CSV-like string for the toast
    error_details = []
    for error in exc.errors():
        field = " -> ".join([str(l) for l in error.get("loc", []) if l != "body"])
        msg = error.get("msg", "Invalid value")
        error_details.append(f"{field}: {msg}")
    
    error_msg = "; ".join(error_details)
    
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return JSONResponse(
            status_code=422,
            content={"status": "error", "message": error_msg}
        )

    referer = request.headers.get("referer", "/")
    sep = "&" if "?" in referer else "?"
    return RedirectResponse(url=f"{referer}{sep}error={error_msg.replace(' ', '+')}", status_code=303)

# Include API Routers with safety guard
try:
    app.include_router(api_router)
except Exception as e:
    logger.critical(f"Failed to include api_router: {e}")

# END FILE
