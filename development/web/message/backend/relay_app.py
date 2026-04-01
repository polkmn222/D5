import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from db import models  # noqa: F401
from db.database import Base, engine, initialize_database_runtime
from web.message.backend.relay_runtime_router import router as relay_runtime_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    startup_started_at = time.perf_counter()
    Base.metadata.create_all(bind=engine)
    initialize_database_runtime()
    logger.info(
        "relay_runtime_startup component=lifespan_create_all duration_ms=%.2f",
        (time.perf_counter() - startup_started_at) * 1000,
    )
    yield


app = FastAPI(title="D5 Relay Runtime", lifespan=lifespan)
app.include_router(relay_runtime_router)


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception):
    logger.error("Relay runtime unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    error_msg = "; ".join(
        [f"{' -> '.join([str(loc) for loc in err.get('loc', [])])}: {err.get('msg')}" for err in exc.errors()]
    )
    return JSONResponse(status_code=422, content={"status": "error", "message": error_msg})
