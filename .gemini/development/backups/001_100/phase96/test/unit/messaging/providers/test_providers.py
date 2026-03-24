from unittest.mock import Mock, patch

from web.message.backend.services.message_providers.base import MessageDispatchPayload
from web.message.backend.services.message_providers.mock_provider import MockMessageProvider
from web.message.backend.services.message_providers.slack_provider import SlackMessageProvider


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


def test_slack_provider_posts_dev_test_payload():
    provider = SlackMessageProvider()
    payload = MessageDispatchPayload(
        contact_id="CON-1",
        record_type="MMS",
        content="Hello",
        subject="Preview",
        template_id="TMP-1",
        image_url="/static/uploads/message_templates/sample.jpg",
        attachment_name="sample.jpg",
    )

    fake_response = Mock(status_code=200, headers={"x-slack-req-id": "req-123"})
    fake_response.text = "ok"

    def getenv_side_effect(key, default=None):
        if key == "SLACK_MESSAGE_WEBHOOK_URL":
            return "https://hooks.slack.test/services/abc"
        if key == "APP_BASE_URL":
            return "https://example.test"
        return default if default is not None else ""

    with patch("os.getenv", side_effect=getenv_side_effect), \
         patch("requests.post", return_value=fake_response) as mock_post:
        result = provider.send(None, payload)

    assert result["status"] == "success"
    assert result["provider"] == "slack"
    sent_json = mock_post.call_args.kwargs["json"]
    assert sent_json["text"] == "MMS dev/test dispatch"
    joined = str(sent_json["blocks"])
    assert "No carrier SMS/LMS/MMS delivery was attempted" in joined
    assert "https://example.test/static/uploads/message_templates/sample.jpg" in joined


def test_slack_provider_skips_image_preview_without_app_base_url():
    provider = SlackMessageProvider()
    payload = MessageDispatchPayload(
        contact_id="CON-2",
        record_type="MMS",
        content="Hello",
        subject="Preview",
        image_url="/static/uploads/message_templates/sample.jpg",
        attachment_name="sample.jpg",
    )

    fake_response = Mock(status_code=200, headers={"x-slack-req-id": "req-456"})
    fake_response.text = "ok"

    def getenv_side_effect(key, default=None):
        if key == "SLACK_MESSAGE_WEBHOOK_URL":
            return "https://hooks.slack.test/services/abc"
        if key == "APP_BASE_URL":
            return ""
        return default if default is not None else ""

    with patch("os.getenv", side_effect=getenv_side_effect), \
         patch("requests.post", return_value=fake_response) as mock_post:
        result = provider.send(None, payload)

    assert result["status"] == "success"
    sent_json = mock_post.call_args.kwargs["json"]
    joined = str(sent_json["blocks"])
    assert "Preview skipped because `APP_BASE_URL` is not configured" in joined
    assert "image_url" not in joined
