from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Attachment
from .base_service import BaseService

logger = logging.getLogger(__name__)

class AttachmentService(BaseService[Attachment]):
    model = Attachment
    object_name = "Attachment"

    @classmethod
    def create_attachment(cls, db: Session, name: str, file_path: str, content_type: str = None, file_size: int = None, parent_id: str = None, parent_type: str = None, provider_key: str = None) -> Attachment:
        return cls.create(db, name=name, file_path=file_path, content_type=content_type, file_size=file_size, parent_id=parent_id, parent_type=parent_type, provider_key=provider_key)

    @classmethod
    def get_attachments_by_parent(cls, db: Session, parent_id: str) -> List[Attachment]:
        return db.query(Attachment).filter(Attachment.parent_id == parent_id, Attachment.deleted_at == None).all()

    @classmethod
    def get_attachment(cls, db: Session, attachment_id: str) -> Optional[Attachment]:
        return cls.get(db, attachment_id)
