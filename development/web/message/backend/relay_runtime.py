import logging
import os
from typing import Optional
from urllib.parse import urlparse, urlunparse

import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

from web.message.backend.services.message_providers.base import MessageDispatchPayload
from web.message.backend.services.message_providers.factory import MessageProviderFactory
from web.message.backend.services.messaging_service import MessagingService

logger = logging.getLogger(__name__)

DEMO_UNAVAILABLE_MESSAGE = "Message service is unavailable. Contact the administrator."


class RelayDispatchRequest(BaseModel):
    contact_id: str
    record_type: str = "SMS"
    content: str
    subject: Optional[str] = None
    template_id: Optional[str] = None
    attachment_id: Optional[str] = None
    attachment_path: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_provider_key: Optional[str] = None
    image_url: Optional[str] = None


def _demo_unavailable_response(reason: Optional[str] = None) -> dict:
    return {
        "available": False,
        "message": DEMO_UNAVAILABLE_MESSAGE,
        "reason": reason or "relay_unavailable",
    }


def _validate_bearer_token(authorization: Optional[str], expected_token: str) -> bool:
    incoming_token = (authorization or "").removeprefix("Bearer ").strip()
    return bool(expected_token) and incoming_token == expected_token


def _relay_target_provider() -> str:
    return os.getenv("RELAY_TARGET_PROVIDER", "").strip().lower() or "surem"


def _provider_ready_for_demo(provider_name: str) -> tuple[bool, Optional[str]]:
    if provider_name == "relay":
        return False, "relay_target_cannot_be_relay"
    if provider_name == "surem":
        required = {
            "SUREM_AUTH_userCode": os.getenv("SUREM_AUTH_userCode", "").strip() or os.getenv("SUREM_USER_CODE", "").strip(),
            "SUREM_AUTH_secretKey": os.getenv("SUREM_AUTH_secretKey", "").strip() or os.getenv("SUREM_SECRET_KEY", "").strip(),
            "SUREM_reqPhone": os.getenv("SUREM_reqPhone", "").strip() or os.getenv("SUREM_REQ_PHONE", "").strip(),
            "SUREM_TO": os.getenv("SUREM_TO", "").strip() or os.getenv("SUREM_FORCE_TO_NUMBER", "").strip(),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            return False, f"missing_demo_provider_env:{','.join(missing)}"
    if provider_name == "slack" and not os.getenv("SLACK_MESSAGE_WEBHOOK_URL", "").strip():
        return False, "missing_demo_provider_env:SLACK_MESSAGE_WEBHOOK_URL"
    return True, None


def _derive_demo_relay_health_url(endpoint: str) -> Optional[str]:
    endpoint = (endpoint or "").strip()
    if not endpoint:
        return None

    parsed = urlparse(endpoint)
    if not parsed.scheme or not parsed.netloc:
        return None

    relay_path = parsed.path.rstrip("/")
    if not relay_path.endswith("/messaging/relay-dispatch"):
        return None

    health_path = f"{relay_path[:-len('/relay-dispatch')]}/demo-relay-health"
    return urlunparse(parsed._replace(path=health_path, params="", query="", fragment=""))


def _normalize_url_for_compare(url: str) -> Optional[tuple[str, str, str]]:
    parsed = urlparse((url or "").strip())
    if not parsed.scheme or not parsed.netloc:
        return None
    path = parsed.path.rstrip("/") or "/"
    return parsed.scheme.lower(), parsed.netloc.lower(), path


def _is_self_relay_endpoint(endpoint: str, current_base_url: str) -> bool:
    current_dispatch_url = f"{(current_base_url or '').rstrip('/')}/messaging/relay-dispatch"
    return _normalize_url_for_compare(endpoint) == _normalize_url_for_compare(current_dispatch_url)


def _local_demo_relay_status() -> dict:
    target_provider = _relay_target_provider()
    provider_ready, reason = _provider_ready_for_demo(target_provider)
    if not provider_ready:
        return _demo_unavailable_response(reason)

    return {
        "available": True,
        "message": "",
        "reason": None,
        "provider": target_provider,
        "mode": "relay",
    }


def _check_remote_demo_relay_health(endpoint: str, token: str) -> dict:
    health_url = _derive_demo_relay_health_url(endpoint)
    if not health_url:
        return _demo_unavailable_response("invalid_relay_endpoint")

    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client() as client:
            response = client.get(health_url, headers=headers, timeout=3)
    except Exception as exc:
        logger.warning("Demo relay availability probe failed: %s", exc)
        return _demo_unavailable_response("relay_health_unreachable")

    if response.status_code >= 400:
        return _demo_unavailable_response(f"relay_health_http_{response.status_code}")

    try:
        payload = response.json()
    except ValueError:
        return _demo_unavailable_response("relay_health_invalid_json")

    if not payload.get("available"):
        return _demo_unavailable_response(payload.get("reason") or "relay_unavailable")

    return {
        "available": True,
        "message": "",
        "reason": None,
        "provider": payload.get("provider"),
        "mode": "relay",
    }


def provider_status_payload() -> dict:
    return {"status": "success", "data": MessageProviderFactory.get_provider_status()}


def demo_relay_health_payload(authorization: Optional[str]) -> tuple[int, dict]:
    expected_token = os.getenv("RELAY_MESSAGE_TOKEN", "").strip()
    if not expected_token:
        return 503, _demo_unavailable_response("relay_token_not_configured")

    if not _validate_bearer_token(authorization, expected_token):
        return 403, _demo_unavailable_response("invalid_relay_token")

    target_provider = _relay_target_provider()
    provider_ready, reason = _provider_ready_for_demo(target_provider)
    if not provider_ready:
        return 503, _demo_unavailable_response(reason)

    return 200, {
        "available": True,
        "message": "",
        "reason": None,
        "provider": target_provider,
    }


def demo_availability_payload(request_base_url: str) -> dict:
    provider_name = MessageProviderFactory.get_provider_name()
    if MessageProviderFactory.render_delivery_blocked():
        return _demo_unavailable_response("render_delivery_blocked")
    if provider_name != "relay":
        return {
            "available": True,
            "message": "",
            "reason": None,
            "mode": "direct",
            "provider": provider_name,
        }

    endpoint = os.getenv("RELAY_MESSAGE_ENDPOINT", "").strip()
    token = os.getenv("RELAY_MESSAGE_TOKEN", "").strip()
    if not endpoint:
        return _demo_unavailable_response("relay_endpoint_not_configured")
    if not token:
        return _demo_unavailable_response("relay_token_not_configured")

    if _is_self_relay_endpoint(endpoint, request_base_url):
        relay_status = _local_demo_relay_status()
        relay_status["provider"] = relay_status.get("provider") or provider_name
        relay_status["mode"] = "relay"
        return relay_status

    relay_status = _check_remote_demo_relay_health(endpoint, token)
    relay_status["provider"] = relay_status.get("provider") or provider_name
    relay_status["mode"] = "relay"
    return relay_status


def relay_dispatch_payload(
    db: Session,
    data: RelayDispatchRequest,
    authorization: Optional[str],
) -> tuple[int, dict]:
    if MessageProviderFactory.render_delivery_blocked():
        return 503, {"status": "error", "message": MessageProviderFactory.render_delivery_block_message()}

    expected_token = os.getenv("RELAY_MESSAGE_TOKEN", "").strip()
    if not expected_token:
        return 500, {"status": "error", "message": "RELAY_MESSAGE_TOKEN is not configured."}

    if not _validate_bearer_token(authorization, expected_token):
        return 403, {"status": "error", "message": "Invalid relay token."}

    target_provider = _relay_target_provider()
    if target_provider == "relay":
        return 400, {"status": "error", "message": "RELAY_TARGET_PROVIDER cannot be relay."}

    payload = MessageDispatchPayload(
        contact_id=data.contact_id,
        record_type=(data.record_type or "SMS").upper(),
        content=data.content,
        subject=data.subject,
        template_id=data.template_id,
        attachment_id=data.attachment_id,
        attachment_path=data.attachment_path,
        attachment_name=data.attachment_name,
        attachment_provider_key=data.attachment_provider_key,
        image_url=data.image_url,
    )
    provider_response = MessagingService._dispatch_payload(db, payload, provider_name_override=target_provider)
    return 200, {"status": "success", "data": provider_response}
