import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base import BaseMessageProvider, MessageDispatchPayload


logger = logging.getLogger(__name__)


class MockMessageProvider(BaseMessageProvider):
    provider_name = "mock"

    def send(self, db: Any, payload: MessageDispatchPayload) -> Dict[str, Any]:
        provider_message_id = f"mock-{payload.record_type.lower()}-{int(datetime.now(timezone.utc).timestamp())}"
        logger.info(
            "Mock message dispatched",
            extra={
                "contact_id": payload.contact_id,
                "record_type": payload.record_type,
                "template_id": payload.template_id,
                "has_image": bool(payload.image_url or payload.attachment_id),
            },
        )
        return {
            "status": "success",
            "provider": self.provider_name,
            "code": "MOCK_OK",
            "provider_message_id": provider_message_id,
            "message": "Mock provider accepted the message.",
        }
