import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base
from backend.app.services.messaging_service import MessagingService
from db.models import Contact, MessageSend, Attachment

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./.gemini/development/test/databases/test_messaging.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Create a dummy contact for testing
    contact = Contact(id="003000000000000001", first_name="Test", last_name="User")
    db.add(contact)
    db.commit()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_send_sms_success(db):
    with patch("backend.app.services.surem_service.SureMService.send_sms") as mock_send_sms:
        mock_send_sms.return_value = {"status": "success", "code": "A0000"}
        
        msg = MessagingService.send_message(db, contact_id="003000000000000001", content="Hello SMS", record_type="SMS")
        
        assert msg is not None
        assert msg.status == "Sent"
        mock_send_sms.assert_called_once_with(text="Hello SMS")

def test_send_lms_success(db):
    with patch("backend.app.services.surem_service.SureMService.send_mms") as mock_send_mms:
        mock_send_mms.return_value = {"status": "success", "code": "A0000"}
        
        msg = MessagingService.send_message(db, contact_id="003000000000000001", content="Hello LMS", record_type="LMS")
        
        assert msg is not None
        assert msg.status == "Sent"
        mock_send_mms.assert_called_once()

def test_send_mms_success_with_attachment(db):
    # Create dummy attachment
    att = Attachment(id="00P000000000000001", name="test.jpg", file_path="static/uploads/test.jpg", provider_key="IMG_KEY_123")
    db.add(att)
    db.commit()
    
    with patch("backend.app.services.surem_service.SureMService.send_mms") as mock_send_mms:
        mock_send_mms.return_value = {"status": "success", "code": "A0000"}
        
        msg = MessagingService.send_message(
            db, 
            contact_id="003000000000000001", 
            content="Hello MMS", 
            record_type="MMS", 
            attachment_id="00P000000000000001"
        )
        
        assert msg is not None
        assert msg.status == "Sent"
        mock_send_mms.assert_called_once_with(subject="GK CRM Message", text="Hello MMS", image_key="IMG_KEY_123")

def test_send_message_failure(db):
    with patch("backend.app.services.surem_service.SureMService.send_sms") as mock_send_sms:
        mock_send_sms.return_value = {"status": "error", "code": "E9999", "message": "Failed"}
        
        with pytest.raises(ValueError, match="Failed to send message via SUREM broker"):
            MessagingService.send_message(db, contact_id="003000000000000001", content="Fail", record_type="SMS")
        
        # Verify MessageSend record was created with status 'Failed'
        msg = db.query(MessageSend).first()
        assert msg.status == "Failed"
