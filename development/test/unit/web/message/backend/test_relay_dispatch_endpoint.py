from unittest.mock import patch

from fastapi.testclient import TestClient

from web.backend.app.main import app


client = TestClient(app)


def test_relay_dispatch_rejects_invalid_token():
    with patch.dict(
        "os.environ",
        {
            "RELAY_MESSAGE_TOKEN": "expected-token",
        },
        clear=False,
    ):
        response = client.post(
            "/messaging/relay-dispatch",
            json={
                "contact_id": "C1",
                "record_type": "SMS",
                "content": "hello",
            },
            headers={"Authorization": "Bearer wrong-token"},
        )

    assert response.status_code == 403
    assert response.json()["message"] == "Invalid relay token."


def test_relay_dispatch_forwards_to_target_provider():
    with patch.dict(
        "os.environ",
        {
            "RELAY_MESSAGE_TOKEN": "expected-token",
            "RELAY_TARGET_PROVIDER": "surem",
        },
        clear=False,
    ), patch(
        "web.message.backend.router.MessagingService._dispatch_payload",
        return_value={
            "status": "success",
            "provider": "surem",
            "provider_message_id": "group-123",
            "message": "accepted",
        },
    ) as mock_dispatch:
        response = client.post(
            "/messaging/relay-dispatch",
            json={
                "contact_id": "C1",
                "record_type": "MMS",
                "content": "hello",
                "image_url": "https://demo.example.com/image.jpg",
            },
            headers={"Authorization": "Bearer expected-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["provider"] == "surem"
    _, kwargs = mock_dispatch.call_args
    payload = mock_dispatch.call_args.args[1]
    assert payload.contact_id == "C1"
    assert payload.record_type == "MMS"
    assert payload.image_url == "https://demo.example.com/image.jpg"
    assert kwargs["provider_name_override"] == "surem"


def test_relay_dispatch_is_blocked_on_render_by_default():
    with patch.dict(
        "os.environ",
        {
            "RENDER_SERVICE_NAME": "d5-app",
            "RELAY_MESSAGE_TOKEN": "expected-token",
            "RELAY_TARGET_PROVIDER": "surem",
        },
        clear=False,
    ):
        response = client.post(
            "/messaging/relay-dispatch",
            json={
                "contact_id": "C1",
                "record_type": "SMS",
                "content": "hello",
            },
            headers={"Authorization": "Bearer expected-token"},
        )

    assert response.status_code == 503
    assert "Contact the administrator" in response.json()["message"]
