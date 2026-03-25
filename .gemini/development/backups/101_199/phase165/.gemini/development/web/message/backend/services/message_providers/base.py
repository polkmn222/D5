from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MessageDispatchPayload:
    contact_id: str
    record_type: str
    content: str
    subject: Optional[str] = None
    template_id: Optional[str] = None
    attachment_id: Optional[str] = None
    attachment_path: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_provider_key: Optional[str] = None
    image_url: Optional[str] = None


class BaseMessageProvider:
    provider_name = "base"

    def send(self, db: Any, payload: MessageDispatchPayload) -> Dict[str, Any]:
        raise NotImplementedError
