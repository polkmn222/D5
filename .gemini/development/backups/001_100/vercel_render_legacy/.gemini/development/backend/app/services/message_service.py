from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import MessageSend as Message
from .base_service import BaseService
from backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class MessageService(BaseService[Message]):
    model = Message
    object_name = "MessageSend"

    @classmethod
    @handle_agent_errors
    def create_message(cls, db: Session, contact: str, content: str, direction: str = "Outbound", status: str = "Sent", **kwargs) -> Message:
        return cls.create(db, contact=contact, content=content, direction=direction, status=status, **kwargs)

    @classmethod
    @handle_agent_errors
    def get_messages(cls, db: Session, contact: Optional[str] = None) -> List[Message]:
        return cls.list(db, contact=contact)

    @classmethod
    @handle_agent_errors
    def get_message(cls, db: Session, message_id: str) -> Optional[Message]:
        return cls.get(db, message_id)

    @classmethod
    @handle_agent_errors
    def update_message(cls, db: Session, message_id: str, **kwargs) -> Optional[Message]:
        return cls.update(db, message_id, **kwargs)

    @classmethod
    @handle_agent_errors
    def delete_message(cls, db: Session, message_id: str) -> bool:
        return cls.delete(db, message_id)
