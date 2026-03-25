import pytest
import uuid
from unittest.mock import patch, MagicMock
from db.database import Base, engine, SessionLocal
from web.backend.app.services.messaging_service import MessagingService
from db.models import Contact, MessageSend, Attachment

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    unique_id = uuid.uuid4().hex[:8]
    # Create a dummy contact for testing
    contact = Contact(id=f"CNT-{unique_id}", first_name="Test", last_name=f"User-{unique_id}")
    db_contact_id = contact.id
    session.add(contact)
    session.commit()
    try:
        session.test_contact_id = db_contact_id
        yield session
    finally:
        session.close()

def test_send_sms_success(db):
    provider = MagicMock()
    provider.provider_name = "mock"
    provider.send.return_value = {"status": "success", "code": "MOCK_OK", "provider_message_id": "mock-1"}
    with patch("web.backend.app.services.messaging_service.MessageProviderFactory.get_provider", return_value=provider):
        
        msg = MessagingService.send_message(db, contact_id=db.test_contact_id, content="Hello SMS", record_type="SMS")
        
        assert msg is not None
        assert msg.status == "Sent"
        assert msg.provider_message_id == "mock-1"
        provider.send.assert_called_once()

def test_send_lms_success(db):
    provider = MagicMock()
    provider.provider_name = "mock"
    provider.send.return_value = {"status": "success", "code": "MOCK_OK", "provider_message_id": "mock-2"}
    with patch("web.backend.app.services.messaging_service.MessageProviderFactory.get_provider", return_value=provider):
        
        msg = MessagingService.send_message(db, contact_id=db.test_contact_id, content="Hello LMS", record_type="LMS")
        
        assert msg is not None
        assert msg.status == "Sent"
        provider.send.assert_called_once()

def test_send_mms_success_with_attachment(db):
    unique_id = uuid.uuid4().hex[:8]
    # Create dummy attachment
    att = Attachment(id=f"ATT-{unique_id}", name="test.jpg", file_path="static/uploads/test.jpg", provider_key=f"IMG_KEY_{unique_id}")
    db.add(att)
    db.commit()
    
    provider = MagicMock()
    provider.provider_name = "mock"
    provider.send.return_value = {"status": "success", "code": "MOCK_OK", "provider_message_id": "mock-3"}
    with patch("web.backend.app.services.messaging_service.MessageProviderFactory.get_provider", return_value=provider):
        
        msg = MessagingService.send_message(
            db, 
            contact_id=db.test_contact_id, 
            content="Hello MMS", 
            record_type="MMS", 
            attachment_id=att.id
        )
        
        assert msg is not None
        assert msg.status == "Sent"
        sent_payload = provider.send.call_args.args[1]
        assert sent_payload.attachment_id == att.id
        assert sent_payload.attachment_provider_key == f"IMG_KEY_{unique_id}"

def test_send_message_failure(db):
    provider = MagicMock()
    provider.provider_name = "mock"
    provider.send.return_value = {"status": "error", "code": "MOCK_FAIL", "message": "Failed"}
    with patch("web.backend.app.services.messaging_service.MessageProviderFactory.get_provider", return_value=provider):
        
        with pytest.raises(ValueError, match="Failed to send message via mock"):
            MessagingService.send_message(db, contact_id=db.test_contact_id, content="Fail", record_type="SMS")
        
        # Verify MessageSend record was created with status 'Failed'
        # Filter by contact_id to be safe in shared DB
        msg = db.query(MessageSend).filter(MessageSend.contact == db.test_contact_id).first()
        assert msg.status == "Failed"
