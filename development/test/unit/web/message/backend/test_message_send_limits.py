import pytest
from unittest.mock import MagicMock, patch
from web.message.backend.services.messaging_service import MessagingService

def test_send_sms_auto_switch_to_lms():
    # > 90 bytes
    content = "가" * 46 
    db = MagicMock()
    contact_id = "CONT_123"
    
    with patch("web.message.backend.services.messaging_service.MessagingService._resolve_message_content", return_value=(content, None, None, None)), \
         patch("web.message.backend.services.messaging_service.MessagingService._merge_context", return_value={"name": "Test", "model": "GV80"}), \
         patch("web.message.backend.services.messaging_service.MessageProviderFactory.get_provider_by_name") as mock_factory, \
         patch("web.message.backend.services.message_service.MessageService.create_message") as mock_create:
        
        mock_provider = MagicMock()
        mock_provider.send.return_value = {"status": "success"}
        mock_provider.provider_name = "Mock"
        mock_factory.return_value = mock_provider
        
        MessagingService.send_message(db, contact_id, content=content, record_type="SMS")
        
        # Verify provider received LMS
        args, _ = mock_provider.send.call_args
        payload = args[1]
        assert payload.record_type == "LMS"

def test_send_byte_limit_2000_violation():
    content = "가" * 1001
    db = MagicMock()
    contact_id = "CONT_123"
    
    with patch("web.message.backend.services.messaging_service.MessagingService._resolve_message_content", return_value=(content, None, None, None)):
        with pytest.raises(ValueError, match="Content exceeds maximum limit"):
            MessagingService.send_message(db, contact_id, content=content)


def test_send_message_records_failed_audit_when_provider_rejects():
    db = MagicMock()
    contact_id = "CONT_123"

    with patch(
        "web.message.backend.services.messaging_service.MessagingService._resolve_message_content",
        return_value=("Hello", None, None, None),
    ), patch(
        "web.message.backend.services.messaging_service.MessagingService._merge_context",
        return_value={"name": "Test", "model": "GV80"},
    ), patch(
        "web.message.backend.services.messaging_service.MessageProviderFactory.get_provider_by_name"
    ) as mock_factory, patch(
        "web.message.backend.services.messaging_service.MessageService.create_message"
    ) as mock_create:
        mock_provider = MagicMock()
        mock_provider.send.return_value = {"status": "error", "provider": "surem", "message": "dispatch failed"}
        mock_provider.provider_name = "surem"
        mock_factory.return_value = mock_provider

        with pytest.raises(ValueError, match="dispatch failed"):
            MessagingService.send_message(db, contact_id, content="Hello", record_type="LMS")

    mock_create.assert_called_once()
    kwargs = mock_create.call_args.kwargs
    assert kwargs["status"] == "Failed"
    assert kwargs["content"] == "Hello"


def test_send_message_records_failed_audit_when_validation_fails_before_dispatch():
    db = MagicMock()
    contact_id = "CONT_123"

    with patch(
        "web.message.backend.services.messaging_service.MessagingService._resolve_message_content",
        side_effect=ValueError("MMS requires attachment"),
    ), patch(
        "web.message.backend.services.messaging_service.MessageService.create_message"
    ) as mock_create:
        with pytest.raises(ValueError, match="MMS requires attachment"):
            MessagingService.send_message(db, contact_id, content="Attempted body", record_type="MMS")

    mock_create.assert_called_once()
    kwargs = mock_create.call_args.kwargs
    assert kwargs["contact"] == contact_id
    assert kwargs["status"] == "Failed"
    assert kwargs["content"] == "Attempted body"


def test_send_message_persists_record_type_subject_and_image_fields():
    db = MagicMock()
    contact_id = "CONT_123"
    attachment = MagicMock()
    attachment.file_path = "/static/uploads/message_templates/test.jpg"
    attachment.name = "test.jpg"
    attachment.provider_key = "img-key"

    with patch(
        "web.message.backend.services.messaging_service.MessagingService._resolve_message_content",
        return_value=("Hello MMS", "Subject", "ATT001", attachment),
    ), patch(
        "web.message.backend.services.messaging_service.MessagingService._merge_context",
        return_value={"name": "Test", "model": "GV80"},
    ), patch(
        "web.message.backend.services.messaging_service.MessageProviderFactory.get_provider_by_name"
    ) as mock_factory, patch(
        "web.message.backend.services.messaging_service.MessageService.create_message"
    ) as mock_create:
        mock_provider = MagicMock()
        mock_provider.send.return_value = {"status": "success", "provider": "surem", "provider_message_id": "msg-1"}
        mock_provider.provider_name = "surem"
        mock_factory.return_value = mock_provider

        MessagingService.send_message(db, contact_id, content="Hello MMS", record_type="MMS", attachment_id="ATT001", subject="Subject")

    kwargs = mock_create.call_args.kwargs
    assert kwargs["record_type"] == "MMS"
    assert kwargs["subject"] == "Subject"
    assert kwargs["attachment_id"] == "ATT001"
    assert kwargs["image_url"] == "/static/uploads/message_templates/test.jpg"


def test_send_message_is_blocked_on_render_by_default():
    db = MagicMock()

    with patch.dict(
        "os.environ",
        {
            "RENDER_SERVICE_NAME": "d5-app",
        },
        clear=False,
    ):
        with pytest.raises(ValueError, match="Contact the administrator"):
            MessagingService.send_message(db, "CONT_123", content="Hello")
