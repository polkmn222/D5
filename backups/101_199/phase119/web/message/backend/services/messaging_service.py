from sqlalchemy.orm import Session
import logging
from .message_service import MessageService
from .message_template_service import MessageTemplateService
from db.models import MessageSend as Message, Attachment
from web.backend.app.utils.error_handler import handle_agent_errors
from typing import List, Optional

from .message_providers.factory import MessageProviderFactory
from .message_providers.base import MessageDispatchPayload

logger = logging.getLogger(__name__)

class MessagingService:
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
        subject: Optional[str] = "GK CRM Message",
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
