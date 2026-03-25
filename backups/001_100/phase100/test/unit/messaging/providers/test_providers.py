import json
from unittest.mock import MagicMock, Mock, patch

from web.message.backend.services.message_providers.base import MessageDispatchPayload
from web.message.backend.services.message_providers.factory import MessageProviderFactory
from web.message.backend.services.message_providers.mock_provider import MockMessageProvider
from web.message.backend.services.message_providers.slack_provider import SlackMessageProvider
from web.message.backend.services.message_providers.solapi_provider import SolapiMessageProvider


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


def test_factory_returns_solapi_provider():
    with patch("os.getenv", return_value="solapi"):
        provider = MessageProviderFactory.get_provider()

    assert isinstance(provider, SolapiMessageProvider)


def test_solapi_provider_posts_sms_payload():
    provider = SolapiMessageProvider()
    payload = MessageDispatchPayload(contact_id="CON-1", record_type="SMS", content="Hello")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock(phone="010-2222-3333")

    send_response = Mock()
    send_response.read.return_value = json.dumps({"groupInfo": {"groupId": "GRP-1", "status": "PENDING"}}).encode()
    send_response.__enter__ = Mock(return_value=send_response)
    send_response.__exit__ = Mock(return_value=None)

    def getenv_side_effect(key, default=None):
        values = {
            "SOLAPI_API_KEY": "api-key",
            "SOLAPI_API_SECRET": "api-secret",
            "SOLAPI_SENDER_NUMBER": "01011112222",
        }
        return values.get(key, default if default is not None else "")

    with patch("os.getenv", side_effect=getenv_side_effect), \
         patch("urllib.request.urlopen", return_value=send_response) as mock_urlopen:
        result = provider.send(db, payload)

    assert result["status"] == "success"
    request = mock_urlopen.call_args.args[0]
    sent_json = json.loads(request.data.decode())
    assert sent_json["messages"][0]["from"] == "01011112222"
    assert sent_json["messages"][0]["to"] == "01022223333"
    assert sent_json["messages"][0]["text"] == "Hello"


def test_solapi_provider_uploads_mms_image_before_send():
    provider = SolapiMessageProvider()
    payload = MessageDispatchPayload(
        contact_id="CON-2",
        record_type="MMS",
        content="Hello",
        subject="Preview",
        image_url="https://example.test/sample.jpg",
        attachment_name="sample.jpg",
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock(phone="01033334444")

    upload_response = Mock()
    upload_response.read.return_value = json.dumps({"fileId": "FILE-123"}).encode()
    upload_response.__enter__ = Mock(return_value=upload_response)
    upload_response.__exit__ = Mock(return_value=None)

    send_response = Mock()
    send_response.read.return_value = json.dumps({"groupInfo": {"groupId": "GRP-2", "status": "PENDING"}}).encode()
    send_response.__enter__ = Mock(return_value=send_response)
    send_response.__exit__ = Mock(return_value=None)

    image_response = Mock()
    image_response.read.return_value = b"jpg-bytes"
    image_response.__enter__ = Mock(return_value=image_response)
    image_response.__exit__ = Mock(return_value=None)

    def getenv_side_effect(key, default=None):
        values = {
            "SOLAPI_API_KEY": "api-key",
            "SOLAPI_API_SECRET": "api-secret",
            "SOLAPI_SENDER_NUMBER": "01011112222",
        }
        return values.get(key, default if default is not None else "")

    with patch("os.getenv", side_effect=getenv_side_effect), \
         patch("urllib.request.urlopen", side_effect=[image_response, upload_response, send_response]) as mock_urlopen:
        result = provider.send(db, payload)

    assert result["status"] == "success"
    upload_request = mock_urlopen.call_args_list[1].args[0]
    upload_json = json.loads(upload_request.data.decode())
    assert upload_json["type"] == "MMS"
    send_request = mock_urlopen.call_args_list[2].args[0]
    send_json = json.loads(send_request.data.decode())
    assert send_json["messages"][0]["imageId"] == "FILE-123"
    assert send_json["messages"][0]["subject"] == "Preview"
