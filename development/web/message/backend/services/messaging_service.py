import logging
from sqlalchemy.orm import Session
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

    @classmethod
    def _guard_render_delivery_policy(cls) -> None:
        if MessageProviderFactory.render_delivery_blocked():
            raise ValueError(MessageProviderFactory.render_delivery_block_message())

    @classmethod
    def _dispatch_payload(
        cls,
        db: Session,
        payload: MessageDispatchPayload,
        provider_name_override: Optional[str] = None,
    ) -> dict:
        provider_name = provider_name_override or MessageProviderFactory.get_provider_name()
        provider = MessageProviderFactory.get_provider_by_name(provider_name)
        return provider.send(db, payload)

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
        # Try to find model from Opportunity first, then fallback to Lead
        opportunity = db.query(Opportunity).filter(Opportunity.contact == contact_id, Opportunity.deleted_at == None).order_by(Opportunity.updated_at.desc(), Opportunity.created_at.desc()).first()
        
        model_id = None
        if opportunity and opportunity.model:
            model_id = opportunity.model
        else:
            # Fallback: check if there's a lead converted to this contact
            from db.models import Lead
            lead = db.query(Lead).filter(Lead.converted_contact == contact_id, Lead.deleted_at == None).first()
            if lead and lead.model:
                model_id = lead.model

        model = db.query(Model).filter(Model.id == model_id, Model.deleted_at == None).first() if model_id else None
        
        first_name = getattr(contact, "first_name", "") or ""
        last_name = getattr(contact, "last_name", "") or ""
        full_name = f"{first_name} {last_name}".strip()
        
        return {
            "name": full_name or getattr(contact, "name", None) or "Customer",
            "customer_name": full_name or getattr(contact, "name", None) or "Customer",
            "model": getattr(model, "name", None) or "our latest model",
        }

    @classmethod
    def _apply_merge_fields(cls, content: str, subject: Optional[str], merge_context: dict[str, str]) -> tuple[str, Optional[str]]:
        resolved_content = content
        resolved_subject = subject
        for key, value in merge_context.items():
            # Support both {name} and {Name}
            for k in [key.lower(), key.capitalize()]:
                resolved_content = resolved_content.replace(f"{{{k}}}", value)
                if resolved_subject:
                    resolved_subject = resolved_subject.replace(f"{{{k}}}", value)
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
        
        # Migration fix: handle old templates folder
        if "/static/uploads/templates/" in file_path:
            file_path = file_path.replace("/static/uploads/templates/", "/static/uploads/message_templates/")
            
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
    def _record_failed_attempt(
        cls,
        db: Session,
        contact_id: str,
        content: Optional[str],
        template_id: Optional[str],
    ) -> None:
        fallback_content = (content or "").strip() or "[Message send failed before dispatch]"
        try:
            MessageService.create_message(
                db,
                contact=contact_id,
                content=fallback_content,
                template=template_id,
                direction="Outbound",
                status="Failed",
            )
        except Exception as audit_exc:
            logger.error("Failed to record message send failure audit row: %s", audit_exc)

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
        resolved_content_for_audit = content
        failure_row_recorded = False
        try:
            cls._guard_render_delivery_policy()
            content, subject, attachment_id, attachment = cls._resolve_message_content(
                db,
                content,
                template_id,
                subject,
                attachment_id,
            )
            resolved_content_for_audit = content

            # Normalize and Validate limits
            byte_len = cls._message_length(content)
            if record_type == "SMS" and byte_len > 90:
                record_type = "LMS"
            
            if byte_len > 2000:
                raise ValueError(f"Content exceeds maximum limit of 2000 bytes (Current: {byte_len} bytes)")

            merge_context = cls._merge_context(db, contact_id)
            content, subject = cls._apply_merge_fields(content, subject, merge_context)
            
            # Ensure shape is consistent after merge
            record_type, subject = cls._validate_message_shape(record_type, content, subject)

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

            provider_response = cls._dispatch_payload(db, payload)
            send_status = "Sent" if provider_response.get("status") == "success" else "Failed"
            if send_status == "Failed":
                logger.error(
                    "%s provider send error: %s",
                    provider_response.get("provider") or MessageProviderFactory.get_provider_name(),
                    provider_response,
                )

            # Create the MessageSend record
            msg = MessageService.create_message(
                db, 
                contact=contact_id, 
                content=content, 
                template=template_id,
                direction="Outbound",
                subject=subject,
                record_type=record_type,
                status=send_status,
                provider_message_id=provider_response.get("provider_message_id"),
                image_url=payload.image_url,
                attachment_id=attachment_id,
                **kwargs
            )
            failure_row_recorded = send_status == "Failed"
            
            logger.info(f"Message {send_status} to contact {contact_id}: {msg.id}")
            
            if send_status == "Failed":
                error_msg = provider_response.get("message", "Unknown provider error.")
                provider_name = provider_response.get("provider") or MessageProviderFactory.get_provider_name()
                raise ValueError(f"Failed to send message via {provider_name}: {error_msg}")
                 
            return msg
        except Exception as e:
            logger.error(f"Critical error in send_message: {e}")
            if not failure_row_recorded:
                cls._record_failed_attempt(
                    db,
                    contact_id=contact_id,
                    content=resolved_content_for_audit,
                    template_id=template_id,
                )
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
