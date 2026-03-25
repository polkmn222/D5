from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.services.surem_service import SureMService
from db.database import Base
from db.models import ServiceToken

TEST_DB_PATH = Path(__file__).resolve().parent.parent / "databases" / "test_surem_service.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_get_access_token_uses_cached_database_token(db, monkeypatch):
    monkeypatch.setenv("SUREM_AUTH_URL", "https://example.com/auth")
    monkeypatch.setenv("SUREM_USER_CODE", "user")
    monkeypatch.setenv("SUREM_SECRET_KEY", "secret")

    cached_token = ServiceToken(
        service_name=SureMService.TOKEN_SERVICE_NAME,
        access_token="cached-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(cached_token)
    db.commit()

    with patch("backend.app.services.surem_service.requests.post") as mock_post:
        token = SureMService.get_access_token(db)

    assert token == "cached-token"
    mock_post.assert_not_called()


def test_get_access_token_refreshes_and_persists(db, monkeypatch):
    monkeypatch.setenv("SUREM_AUTH_URL", "https://example.com/auth")
    monkeypatch.setenv("SUREM_USER_CODE", "user")
    monkeypatch.setenv("SUREM_SECRET_KEY", "secret")
    monkeypatch.delenv("SUREM_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("SUREM_TOKEN_EXPIRES_AT", raising=False)

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "code": "A0000",
        "data": {
            "accessToken": "fresh-token",
            "expiresIn": 900,
        },
    }

    with patch("backend.app.services.surem_service.requests.post", return_value=response) as mock_post:
        token = SureMService.get_access_token(db)

    db.expire_all()
    stored_token = db.query(ServiceToken).filter(ServiceToken.service_name == SureMService.TOKEN_SERVICE_NAME).first()

    assert token == "fresh-token"
    assert stored_token is not None
    assert stored_token.access_token == "fresh-token"
    assert stored_token.expires_at is not None
    mock_post.assert_called_once()


def test_debug_auth_status_reports_missing_credentials(db, monkeypatch):
    monkeypatch.delenv("SUREM_AUTH_URL", raising=False)
    monkeypatch.delenv("SUREM_USER_CODE", raising=False)
    monkeypatch.delenv("SUREM_SECRET_KEY", raising=False)
    monkeypatch.delenv("SUREM_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("SUREM_TOKEN_EXPIRES_AT", raising=False)

    result = SureMService.debug_auth_status(db)

    assert result["status"] == "error"
    assert result["error"] == "missing_credentials"
    assert result["auth_url_present"] is False
    assert result["user_code_present"] is False
    assert result["secret_key_present"] is False


def test_send_sms_uses_broker_when_configured(db, monkeypatch):
    monkeypatch.setenv("SUREM_BROKER_URL", "https://broker.example.com")
    monkeypatch.setenv("SUREM_BROKER_SECRET", "shared-secret")

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"status": "success", "code": "A0000"}

    with patch("backend.app.services.surem_service.requests.request", return_value=response) as mock_request:
        result = SureMService.send_sms(db, "broker sms")

    assert result["status"] == "success"
    mock_request.assert_called_once()
    args, kwargs = mock_request.call_args
    assert args[0] == "POST"
    assert args[1] == "https://broker.example.com/api/test/broker/send-sms"
    assert kwargs["headers"]["X-Broker-Secret"] == "shared-secret"
