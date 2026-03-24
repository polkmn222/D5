import pytest
import uuid
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, engine, SessionLocal
from backend.app.services.messaging_service import MessagingService
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
    with patch("backend.app.services.surem_service.SureMService.send_sms") as mock_send_sms:
        mock_send_sms.return_value = {"status": "success", "code": "A0000"}
        
        msg = MessagingService.send_message(db, contact_id=db.test_contact_id, content="Hello SMS", record_type="SMS")
        
        assert msg is not None
        assert msg.status == "Sent"
        mock_send_sms.assert_called_once_with(db, text="Hello SMS")

def test_send_lms_success(db):
    with patch("backend.app.services.surem_service.SureMService.send_mms") as mock_send_mms:
        mock_send_mms.return_value = {"status": "success", "code": "A0000"}
        
        msg = MessagingService.send_message(db, contact_id=db.test_contact_id, content="Hello LMS", record_type="LMS")
        
        assert msg is not None
        assert msg.status == "Sent"
        mock_send_mms.assert_called_once_with(db, subject="GK CRM Message", text="Hello LMS", image_key=None)

def test_send_mms_success_with_attachment(db):
    unique_id = uuid.uuid4().hex[:8]
    # Create dummy attachment
    att = Attachment(id=f"ATT-{unique_id}", name="test.jpg", file_path="static/uploads/test.jpg", provider_key=f"IMG_KEY_{unique_id}")
    db.add(att)
    db.commit()
    
    with patch("backend.app.services.surem_service.SureMService.send_mms") as mock_send_mms:
        mock_send_mms.return_value = {"status": "success", "code": "A0000"}
        
        msg = MessagingService.send_message(
            db, 
            contact_id=db.test_contact_id, 
            content="Hello MMS", 
            record_type="MMS", 
            attachment_id=att.id
        )
        
        assert msg is not None
        assert msg.status == "Sent"
        mock_send_mms.assert_called_once_with(db, subject="GK CRM Message", text="Hello MMS", image_key=f"IMG_KEY_{unique_id}")

def test_send_message_failure(db):
    with patch("backend.app.services.surem_service.SureMService.send_sms") as mock_send_sms:
        mock_send_sms.return_value = {"status": "error", "code": "E9999", "message": "Failed"}
        
        with pytest.raises(ValueError, match="Failed to send message via SUREM broker"):
            MessagingService.send_message(db, contact_id=db.test_contact_id, content="Fail", record_type="SMS")
        
        # Verify MessageSend record was created with status 'Failed'
        # Filter by contact_id to be safe in shared DB
        msg = db.query(MessageSend).filter(MessageSend.contact == db.test_contact_id).first()
        assert msg.status == "Failed"
