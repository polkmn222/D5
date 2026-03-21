from sqlalchemy.orm import Session
import logging
import os
from .message_service import MessageService
from .message_template_service import MessageTemplateService
from .attachment_service import AttachmentService
from .surem_service import SureMService
from db.models import MessageSend as Message, Attachment
from .base_service import BaseService
from backend.app.utils.error_handler import handle_agent_errors
from typing import List, Optional

logger = logging.getLogger(__name__)

class MessagingService:
    @classmethod
    @handle_agent_errors
    def send_message(cls, db: Session, contact_id: str, content: str = None, template_id: str = None, record_type: str = "SMS", attachment_id: str = None, subject: str = "GK CRM Message", **kwargs) -> Optional[Message]:
        """
        Atomized logic for sending a message using SUREM APIs.
        """
        try:
            # If template is provided but no content, fetch content from template
            if template_id and not content:
                template = MessageTemplateService.get_template(db, template_id)
                if template:
                    content = template.content
                    if not attachment_id and template.attachment_id:
                        attachment_id = template.attachment_id
            
            if not content:
                raise ValueError("Message content is required.")

            send_status = "Failed"
            surem_response = None
            
            if record_type == "SMS":
                # User mandate: SMS is fixed to 01033903190 (handled inside SureMService)
                surem_response = SureMService.send_sms(db, text=content)
            elif record_type in ["LMS", "MMS"]:
                image_key = None
                if record_type == "MMS" and attachment_id:
                    attachment = db.query(Attachment).filter(Attachment.id == attachment_id, Attachment.deleted_at == None).first()
                    if attachment:
                        # NEW: Reuse existing provider_key if available
                        if attachment.provider_key:
                            image_key = attachment.provider_key
                            logger.info(f"Reusing existing SUREM Image Key for attachment {attachment_id}: {image_key}")
                        elif attachment.file_path:
                            # Fallback to upload if no provider_key
                            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                            abs_file_path = os.path.join(base_dir, attachment.file_path.lstrip('/'))
                            
                            if os.path.exists(abs_file_path):
                                with open(abs_file_path, 'rb') as f:
                                    file_content = f.read()
                                filename = os.path.basename(abs_file_path)
                                upload_res = SureMService.upload_image(db, file_content, filename)
                                if upload_res.get("status") == "success":
                                    image_key = upload_res.get("data", {}).get("imageKey")
                                    # Update attachment with the new key for future use
                                    attachment.provider_key = image_key
                                    db.commit()
                                else:
                                    logger.error(f"Failed to upload image to SureM: {upload_res}")
                
                # Subject is required for LMS/MMS. Take first 20 chars of content if none provided.
                actual_subject = subject
                if not actual_subject or len(actual_subject) == 0:
                    actual_subject = (content[:20] + '...') if len(content) > 20 else content
                
                # User mandate: LMS/MMS is fixed to 01097343368 (handled inside SureMService)
                surem_response = SureMService.send_mms(db, subject=actual_subject, text=content, image_key=image_key)
            
            if surem_response and surem_response.get("status") == "success" and surem_response.get("code") == "A0000":
                send_status = "Sent"
            else:
                send_status = "Failed"
                logger.error(f"SUREM send error: {surem_response}")

            # Create the MessageSend record
            msg = MessageService.create_message(
                db, 
                contact=contact_id, 
                content=content, 
                template=template_id,
                direction="Outbound",
                status=send_status,
                **kwargs
            )
            
            logger.info(f"Message {send_status} to contact {contact_id}: {msg.id}")
            
            if send_status == "Failed":
                error_msg = surem_response.get("message", "Unknown error") if surem_response else "No response from SUREM broker."
                raise ValueError(f"Failed to send message via SUREM broker: {error_msg}")
                
            return msg
        except Exception as e:
            logger.error(f"Critical error in send_message: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def bulk_send(cls, db: Session, contact_ids: List[str], content: str = None, template_id: str = None, record_type: str = "SMS", attachment_id: str = None, subject: str = None) -> int:
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
