import logging
import os
from typing import Any, Dict, List

import requests

from .base import BaseMessageProvider, MessageDispatchPayload


logger = logging.getLogger(__name__)


class SlackMessageProvider(BaseMessageProvider):
    provider_name = "slack"

    @staticmethod
    def _absolute_image_url(image_url: str) -> str:
        if image_url.startswith("http://") or image_url.startswith("https://"):
            return image_url
        base_url = os.getenv("APP_BASE_URL", "").strip().rstrip("/")
        if base_url and image_url.startswith("/"):
            return f"{base_url}{image_url}"
        return image_url

    def send(self, db: Any, payload: MessageDispatchPayload) -> Dict[str, Any]:
        webhook_url = os.getenv("SLACK_MESSAGE_WEBHOOK_URL", "").strip()
        if not webhook_url:
            return {
                "status": "error",
                "provider": self.provider_name,
                "message": "SLACK_MESSAGE_WEBHOOK_URL is not configured.",
            }

        blocks: List[Dict[str, Any]] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{payload.record_type} test dispatch*\n"
                        f"Contact: `{payload.contact_id}`\n"
                        f"Template: `{payload.template_id or 'custom'}`"
                    ),
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Subject*\n{payload.subject or '-'}\n\n*Content*\n{payload.content}",
                },
            },
        ]

        if payload.image_url:
            image_url = self._absolute_image_url(payload.image_url)
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Image*\n{image_url}"},
                    "accessory": {
                        "type": "image",
                        "image_url": image_url,
                        "alt_text": payload.attachment_name or "message image",
                    },
                }
            )

        response = requests.post(
            webhook_url,
            json={"text": f"{payload.record_type} test dispatch", "blocks": blocks},
            timeout=10,
        )
        if response.status_code >= 400:
            logger.error("Slack provider send failed: %s %s", response.status_code, response.text)
            return {
                "status": "error",
                "provider": self.provider_name,
                "message": response.text or f"Slack webhook error ({response.status_code}).",
            }

        return {
            "status": "success",
            "provider": self.provider_name,
            "code": "SLACK_OK",
            "provider_message_id": response.headers.get("x-slack-req-id") or "slack-webhook",
            "message": "Slack provider accepted the message.",
        }
