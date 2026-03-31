from unittest.mock import MagicMock, patch

from web.message.backend.services.message_providers.base import MessageDispatchPayload
from web.message.backend.services.message_providers.relay_provider import RelayMessageProvider


def test_relay_provider_requires_endpoint():
    provider = RelayMessageProvider()
    payload = MessageDispatchPayload(contact_id="C1", record_type="SMS", content="hello")
    with patch.dict("os.environ", {"RELAY_MESSAGE_ENDPOINT": "", "RELAY_MESSAGE_TOKEN": "token"}, clear=False):
        response = provider.send(None, payload)
    assert response["status"] == "error"
    assert "RELAY_MESSAGE_ENDPOINT" in response["message"]


def test_relay_provider_sends_with_bearer_token():
    provider = RelayMessageProvider()
    payload = MessageDispatchPayload(
        contact_id="C1",
        record_type="MMS",
        content="hello",
        image_url="/static/uploads/message_templates/test.jpg",
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "data": {
            "status": "success",
            "provider": "surem",
            "provider_message_id": "group-1",
            "message": "accepted",
        },
    }
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.post.return_value = mock_response

    with patch.dict(
        "os.environ",
        {
            "RELAY_MESSAGE_ENDPOINT": "https://relay.example.com/messaging/relay-dispatch",
            "RELAY_MESSAGE_TOKEN": "secret",
            "APP_BASE_URL": "https://demo.example.com",
        },
        clear=False,
    ), patch("web.message.backend.services.message_providers.relay_provider.httpx.Client", return_value=mock_client):
        response = provider.send(None, payload)

    assert response["status"] == "success"
    _, kwargs = mock_client.post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer secret"
    assert kwargs["json"]["image_url"] == "https://demo.example.com/static/uploads/message_templates/test.jpg"
