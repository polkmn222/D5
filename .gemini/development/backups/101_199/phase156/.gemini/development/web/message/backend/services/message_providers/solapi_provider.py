import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from db.models import Contact

from .base import BaseMessageProvider, MessageDispatchPayload


class SolapiMessageProvider(BaseMessageProvider):
    provider_name = "solapi"
    API_BASE_URL = "https://api.solapi.com"

    @staticmethod
    def _env(name: str) -> str:
        return os.getenv(name, "").strip()

    @classmethod
    def _create_auth_header(cls) -> str:
        api_key = cls._env("SOLAPI_API_KEY")
        api_secret = cls._env("SOLAPI_API_SECRET")
        if not api_key or not api_secret:
            raise ValueError("SOLAPI_API_KEY and SOLAPI_API_SECRET must be configured.")

        date_time = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        salt = secrets.token_hex(16)
        signature = hmac.new(api_secret.encode(), f"{date_time}{salt}".encode(), hashlib.sha256).hexdigest()
        return f"HMAC-SHA256 apiKey={api_key}, date={date_time}, salt={salt}, signature={signature}"

    @staticmethod
    def _normalize_phone(value: Optional[str]) -> str:
        return re.sub(r"\D", "", value or "")

    @classmethod
    def _resolve_sender(cls) -> str:
        sender = cls._normalize_phone(cls._env("SOLAPI_SENDER_NUMBER"))
        if not sender:
            raise ValueError("SOLAPI_SENDER_NUMBER must be configured with a registered sender number.")
        return sender

    @classmethod
    def _resolve_recipient(cls, db: Any, contact_id: str) -> str:
        forced_number = cls._normalize_phone(cls._env("SOLAPI_FORCE_TO_NUMBER"))
        if forced_number:
            return forced_number
        if db is None:
            raise ValueError("Database session is required for the Solapi provider.")
        contact = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at == None).first()
        phone = cls._normalize_phone(getattr(contact, "phone", None)) if contact else ""
        if not phone:
            raise ValueError(f"Contact {contact_id} does not have a valid phone number.")
        return phone

    @staticmethod
    def _local_upload_root() -> Path:
        return Path(__file__).resolve().parents[4] / "app" / "static"

    @classmethod
    def _read_attachment_bytes(cls, payload: MessageDispatchPayload) -> tuple[bytes, str]:
        source = payload.attachment_path or payload.image_url or ""
        filename = payload.attachment_name or "message-image.jpg"
        if source.startswith("http://") or source.startswith("https://"):
            with urllib.request.urlopen(source, timeout=20) as response:
                return response.read(), filename
        if source.startswith("/static/"):
            local_path = cls._local_upload_root() / source.removeprefix("/static/")
            return local_path.read_bytes(), filename
        raise ValueError("MMS attachment could not be resolved for Solapi upload.")

    @classmethod
    def _upload_mms_image(cls, payload: MessageDispatchPayload) -> str:
        file_bytes, filename = cls._read_attachment_bytes(payload)
        if len(file_bytes) > 200 * 1024:
            raise ValueError("Solapi MMS images must be 200KB or smaller.")

        body = json.dumps(
            {
                "file": base64.b64encode(file_bytes).decode(),
                "name": filename,
                "type": "MMS",
            }
        ).encode()
        request = urllib.request.Request(
            url=f"{cls.API_BASE_URL}/storage/v1/files",
            data=body,
            headers={
                "Authorization": cls._create_auth_header(),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload_json = json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="ignore")
            raise ValueError(detail or "Solapi MMS image upload failed.") from exc

        file_id = payload_json.get("fileId")
        if not file_id:
            raise ValueError("Solapi MMS image upload did not return a fileId.")
        return file_id

    @classmethod
    def _build_message(cls, db: Any, payload: MessageDispatchPayload) -> Dict[str, Any]:
        message: Dict[str, Any] = {
            "to": cls._resolve_recipient(db, payload.contact_id),
            "from": cls._resolve_sender(),
            "text": payload.content,
        }
        if payload.record_type in {"LMS", "MMS"} and payload.subject:
            message["subject"] = payload.subject
        if payload.record_type == "MMS":
            message["imageId"] = cls._upload_mms_image(payload)
        return message

    @classmethod
    def _post_json(cls, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(data).encode()
        request = urllib.request.Request(
            url=f"{cls.API_BASE_URL}{path}",
            data=body,
            headers={
                "Authorization": cls._create_auth_header(),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="ignore")
            raise ValueError(detail or "Solapi send request failed.") from exc

    def send(self, db: Any, payload: MessageDispatchPayload) -> Dict[str, Any]:
        request_payload = {
            "messages": [self._build_message(db, payload)],
            "allowDuplicates": False,
        }
        response = self._post_json("/messages/v4/send-many/detail", request_payload)
        failed_messages = response.get("failedMessageList") or []
        if failed_messages:
            failed = failed_messages[0]
            return {
                "status": "error",
                "provider": self.provider_name,
                "message": failed.get("statusMessage") or failed.get("errorMessage") or "Solapi rejected the message.",
                "provider_message_id": failed.get("messageId"),
            }

        group_info = response.get("groupInfo") or {}
        return {
            "status": "success",
            "provider": self.provider_name,
            "code": group_info.get("status") or "SOLAPI_OK",
            "provider_message_id": group_info.get("groupId") or "solapi-send",
            "message": "Solapi accepted the message.",
        }
