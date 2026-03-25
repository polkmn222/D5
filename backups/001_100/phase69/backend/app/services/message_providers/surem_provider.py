import logging
import os
from typing import Any, Dict, Optional

from db.models import Attachment

from backend.app.services.surem_service import SureMService

from .base import BaseMessageProvider, MessageDispatchPayload


logger = logging.getLogger(__name__)


class SureMMessageProvider(BaseMessageProvider):
    provider_name = "surem"

    def _resolve_image_key(self, db: Any, payload: MessageDispatchPayload) -> Optional[str]:
        if payload.record_type != "MMS" or not payload.attachment_id:
            return None

        attachment = db.query(Attachment).filter(Attachment.id == payload.attachment_id, Attachment.deleted_at == None).first()
        if not attachment:
            return None
        if attachment.provider_key:
            return attachment.provider_key

        file_path = getattr(attachment, "file_path", None)
        if not file_path:
            return None

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_file_path = os.path.join(base_dir, file_path.lstrip('/'))
        if not os.path.exists(abs_file_path):
            return None

        with open(abs_file_path, 'rb') as handle:
            file_content = handle.read()
        filename = os.path.basename(abs_file_path)
        upload_res = SureMService.upload_image(db, file_content, filename)
        if upload_res.get("status") == "success":
            image_key = upload_res.get("data", {}).get("imageKey")
            if image_key:
                attachment.provider_key = image_key
                db.commit()
            return image_key

        logger.error("Failed to upload image to SureM: %s", upload_res)
        return None

    def send(self, db: Any, payload: MessageDispatchPayload) -> Dict[str, Any]:
        if payload.record_type == "SMS":
            result = SureMService.send_sms(db, text=payload.content)
        else:
            subject = payload.subject or ((payload.content[:20] + '...') if len(payload.content) > 20 else payload.content)
            image_key = self._resolve_image_key(db, payload)
            result = SureMService.send_mms(db, subject=subject, text=payload.content, image_key=image_key)

        if result.get("status") == "success" and result.get("code") == "A0000":
            provider_message_id = (
                result.get("data", {}).get("messageId")
                or result.get("data", {}).get("requestId")
                or result.get("code")
            )
            return {
                "status": "success",
                "provider": self.provider_name,
                "code": result.get("code"),
                "provider_message_id": provider_message_id,
                "message": "SureM provider accepted the message.",
                "raw": result,
            }

        return {
            "status": "error",
            "provider": self.provider_name,
            "code": result.get("code"),
            "message": result.get("message", "Unknown SureM error."),
            "raw": result,
        }
