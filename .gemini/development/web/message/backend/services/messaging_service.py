from sqlalchemy.orm import Session
import logging
from .message_service import MessageService
from .message_template_service import MessageTemplateService
from db.models import MessageSend as Message, Attachment, Contact, Opportunity, Model
from web.backend.app.utils.error_handler import handle_agent_errors
from typing import List, Optional

from .message_providers.factory import MessageProviderFactory
from .message_providers.base import MessageDispatchPayload

logger = logging.getLogger(__name__)

class MessagingService:
    SMS_LIMIT = 90
    LMS_MMS_LIMIT = 2000

    @staticmethod
    def _message_length(value: Optional[str]) -> int:
        return len((value or "").encode("utf-8"))

    @classmethod
    def _normalize_record_type(cls, record_type: str, content: str) -> str:
        normalized = (record_type or "SMS").upper()
        if normalized == "SMS" and cls._message_length(content) > cls.SMS_LIMIT:
            return "LMS"
        return normalized

    @staticmethod
    def _merge_context(db: Session, contact_id: str) -> dict[str, str]:
        contact = db.query(Contact).filter(Contact.id == contact_id, Contact.deleted_at == None).first()
        opportunity = db.query(Opportunity).filter(Opportunity.contact == contact_id, Opportunity.deleted_at == None).order_by(Opportunity.updated_at.desc(), Opportunity.created_at.desc()).first()
        model = db.query(Model).filter(Model.id == opportunity.model, Model.deleted_at == None).first() if opportunity and opportunity.model else None
        full_name = " ".join(part for part in [getattr(contact, "first_name", None), getattr(contact, "last_name", None)] if part).strip()
        return {
            "Name": full_name or getattr(contact, "name", None) or "there",
            "Model": getattr(model, "name", None) or "our latest model",
        }

    @classmethod
    def _apply_merge_fields(cls, content: str, subject: Optional[str], merge_context: dict[str, str]) -> tuple[str, Optional[str]]:
        resolved_content = content
        resolved_subject = subject
        for key, value in merge_context.items():
            resolved_content = resolved_content.replace(f"{{{key}}}", value)
            if resolved_subject:
                resolved_subject = resolved_subject.replace(f"{{{key}}}", value)
        return resolved_content, resolved_subject

    @classmethod
    def _validate_message_shape(cls, record_type: str, content: str, subject: Optional[str]) -> tuple[str, Optional[str]]:
        normalized_type = cls._normalize_record_type(record_type, content)
        if normalized_type == "SMS":
            return normalized_type, None

        if cls._message_length(content) > cls.LMS_MMS_LIMIT:
            raise ValueError("LMS and MMS content must be 2000 bytes or fewer.")

        return normalized_type, subject

    @staticmethod
    def _resolve_image_url(attachment: Optional[object]) -> Optional[str]:
        file_path = getattr(attachment, "file_path", None)
        if not file_path:
            return None
        if file_path.startswith("/static/") or file_path.startswith("http://") or file_path.startswith("https://"):
            return file_path
        return None

    @staticmethod
    def _resolve_message_content(
        db: Session,
        content: Optional[str],
        template_id: Optional[str],
        subject: Optional[str],
        attachment_id: Optional[str],
    ) -> tuple[str, Optional[str], Optional[str], Optional[object]]:
        template = None
        resolved_content = content
        resolved_subject = subject
        resolved_attachment_id = attachment_id

        if template_id and not resolved_content:
            template = MessageTemplateService.get_template(db, template_id)
            if template:
                resolved_content = template.content
                if not resolved_attachment_id and template.attachment_id:
                    resolved_attachment_id = template.attachment_id
                if not resolved_subject and template.subject:
                    resolved_subject = template.subject

        if not resolved_content:
            raise ValueError("Message content is required.")

        attachment = None
        if resolved_attachment_id:
            attachment = db.query(Attachment).filter(Attachment.id == resolved_attachment_id, Attachment.deleted_at == None).first()

        return resolved_content, resolved_subject, resolved_attachment_id, attachment

    @classmethod
    @handle_agent_errors
    def send_message(
        cls,
        db: Session,
        contact_id: str,
        content: Optional[str] = None,
        template_id: Optional[str] = None,
        record_type: str = "SMS",
        attachment_id: Optional[str] = None,
        subject: Optional[str] = None,
        **kwargs,
    ) -> Optional[Message]:
        """
        Provider-driven message dispatch with mock/slack/test-safe defaults.
        """
        try:
            content, subject, attachment_id, attachment = cls._resolve_message_content(
                db,
                content,
                template_id,
                subject,
                attachment_id,
            )

            merge_context = cls._merge_context(db, contact_id)
            content, subject = cls._apply_merge_fields(content, subject, merge_context)
            record_type, subject = cls._validate_message_shape(record_type, content, subject)

            provider = MessageProviderFactory.get_provider()
            payload = MessageDispatchPayload(
                contact_id=contact_id,
                record_type=record_type,
                content=content,
                subject=subject,
                template_id=template_id,
                attachment_id=attachment_id,
                attachment_path=getattr(attachment, "file_path", None),
                attachment_name=getattr(attachment, "name", None),
                attachment_provider_key=getattr(attachment, "provider_key", None),
                image_url=cls._resolve_image_url(attachment),
            )

            provider_response = provider.send(db, payload)
            send_status = "Sent" if provider_response.get("status") == "success" else "Failed"
            if send_status == "Failed":
                logger.error("%s provider send error: %s", provider.provider_name, provider_response)

            # Create the MessageSend record
            msg = MessageService.create_message(
                db, 
                contact=contact_id, 
                content=content, 
                template=template_id,
                direction="Outbound",
                status=send_status,
                provider_message_id=provider_response.get("provider_message_id"),
                **kwargs
            )
            
            logger.info(f"Message {send_status} to contact {contact_id}: {msg.id}")
            
            if send_status == "Failed":
                error_msg = provider_response.get("message", "Unknown provider error.")
                raise ValueError(f"Failed to send message via {provider.provider_name}: {error_msg}")
                 
            return msg
        except Exception as e:
            logger.error(f"Critical error in send_message: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def bulk_send(
        cls,
        db: Session,
        contact_ids: List[str],
        content: Optional[str] = None,
        template_id: Optional[str] = None,
        record_type: str = "SMS",
        attachment_id: Optional[str] = None,
        subject: Optional[str] = None,
    ) -> int:
        """
        Send messages to multiple contacts.
        """
        try:
            count = 0
            for cid in contact_ids:
                try:
                    MessagingService.send_message(db, cid, template_id=template_id, content=content, record_type=record_type, attachment_id=attachment_id, subject=subject)
                    count += 1
                except Exception as e:
                    logger.error(f"Bulk send failed for contact {cid}: {e}")
            
            if count == 0 and len(contact_ids) > 0:
                raise ValueError("All message dispatch attempts failed.")
                
            return count
        except Exception as e:
            logger.error(f"Critical error in bulk_send: {e}")
            raise e
