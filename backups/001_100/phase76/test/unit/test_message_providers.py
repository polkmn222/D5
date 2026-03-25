from unittest.mock import patch

from web.backend.app.services.message_providers.base import MessageDispatchPayload
from web.backend.app.services.message_providers.mock_provider import MockMessageProvider
from web.backend.app.services.message_providers.slack_provider import SlackMessageProvider


def test_mock_provider_returns_success_response():
    provider = MockMessageProvider()
    payload = MessageDispatchPayload(contact_id="CON-1", record_type="SMS", content="Hello")

    result = provider.send(None, payload)

    assert result["status"] == "success"
    assert result["provider"] == "mock"
    assert result["provider_message_id"].startswith("mock-sms-")


def test_slack_provider_returns_error_without_webhook():
    provider = SlackMessageProvider()
    payload = MessageDispatchPayload(contact_id="CON-1", record_type="LMS", content="Hello")

    with patch("os.getenv", return_value=""):
        result = provider.send(None, payload)

    assert result["status"] == "error"
    assert "SLACK_MESSAGE_WEBHOOK_URL" in result["message"]
