from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import MessageTemplate
from .base_service import BaseService
from backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class MessageTemplateService(BaseService[MessageTemplate]):
    model = MessageTemplate
    object_name = "MessageTemplate"

    @classmethod
    @handle_agent_errors
    def create_template(cls, db: Session, name: str, content: str, subject: Optional[str] = None, record_type: str = "SMS", file_path: Optional[str] = None, attachment_id: Optional[str] = None, image_url: Optional[str] = None) -> MessageTemplate:
        return cls.create(db, name=name, content=content, subject=subject, record_type=record_type, file_path=file_path, attachment_id=attachment_id, image_url=image_url)

    @classmethod
    @handle_agent_errors
    def get_templates(cls, db: Session) -> List[MessageTemplate]:
        return cls.list(db)

    @classmethod
    @handle_agent_errors
    def get_template(cls, db: Session, template_id: str) -> Optional[MessageTemplate]:
        return cls.get(db, template_id)

    @classmethod
    @handle_agent_errors
    def update_template(cls, db: Session, template_id: str, **kwargs) -> Optional[MessageTemplate]:
        return cls.update(db, template_id, **kwargs)

    @classmethod
    @handle_agent_errors
    def update_image_url(cls, db: Session, template_id: str, image_url: str) -> Optional[MessageTemplate]:
        return cls.update(db, template_id, image_url=image_url)

    @classmethod
    @handle_agent_errors
    def delete_template(cls, db: Session, template_id: str) -> bool:
        return cls.delete(db, template_id)

    @classmethod
    @handle_agent_errors
    def restore_template(cls, db: Session, template_id: str) -> bool:
        return cls.delete(db, template_id)
