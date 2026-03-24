import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost/d4_test")

APP_ROOT = Path(__file__).resolve().parents[2]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from backend.app.services.surem_service import SureMService
from db.models import ServiceToken

class FakeTokenQuery:
    def __init__(self, store):
        self.store = store
        self.service_name = None

    def filter(self, *conditions):
        for condition in conditions:
            right = getattr(condition, "right", None)
            value = getattr(right, "value", None)
            if value is not None:
                self.service_name = value
        return self

    def first(self):
        if self.service_name is None:
            return next(iter(self.store.values()), None)
        return self.store.get(self.service_name)


class FakeSession:
    def __init__(self):
        self.tokens = {}
        self.commits = 0
        self.rollbacks = 0
        self.executed = []
        self.bind = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    def get_bind(self):
        return self.bind

    def execute(self, statement, params=None):
        self.executed.append((str(statement), params or {}))
        return None

    def query(self, _model):
        return FakeTokenQuery(self.tokens)

    def add(self, row):
        self.tokens[row.service_name] = row

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


@pytest.fixture
def db():
    return FakeSession()


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
    stored_token = db.query(ServiceToken).filter(ServiceToken.service_name == SureMService.TOKEN_SERVICE_NAME).first()

    assert token == "fresh-token"
    assert stored_token is not None
    assert stored_token.access_token == "fresh-token"
    assert stored_token.expires_at is not None
    mock_post.assert_called_once()
    assert db.commits == 1


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
