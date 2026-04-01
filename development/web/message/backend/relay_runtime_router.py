import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from db.database import get_db
from web.message.backend.relay_runtime import (
    RelayDispatchRequest,
    demo_availability_payload,
    demo_relay_health_payload,
    provider_status_payload,
    relay_dispatch_payload,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def relay_healthcheck():
    return {"status": "ok", "service": "relay-runtime"}


@router.get("/messaging/provider-status")
async def provider_status():
    try:
        return provider_status_payload()
    except Exception as exc:
        logger.error("Error reading provider status: %s", exc)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})


@router.get("/messaging/demo-relay-health")
async def demo_relay_health(authorization: Optional[str] = Header(default=None)):
    status_code, payload = demo_relay_health_payload(authorization)
    if status_code != 200:
        return JSONResponse(status_code=status_code, content=payload)
    return payload


@router.get("/messaging/demo-availability")
async def demo_availability(request: Request):
    return demo_availability_payload(str(request.base_url))


@router.post("/messaging/relay-dispatch")
async def relay_dispatch(
    data: RelayDispatchRequest,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    try:
        status_code, payload = relay_dispatch_payload(db, data, authorization)
        if status_code != 200:
            return JSONResponse(status_code=status_code, content=payload)
        return payload
    except Exception as exc:
        logger.error("Error in relay dispatch: %s", exc)
        return JSONResponse(status_code=500, content={"status": "error", "message": str(exc)})
