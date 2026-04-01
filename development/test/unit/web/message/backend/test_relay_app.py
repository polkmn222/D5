from unittest.mock import patch

from fastapi.testclient import TestClient

from web.message.backend.relay_app import app


client = TestClient(app)


def test_relay_app_exposes_healthcheck():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "relay-runtime"}


def test_relay_app_limits_surface_and_does_not_serve_messaging_ui():
    response = client.get("/messaging/ui")

    assert response.status_code == 404


def test_relay_app_exposes_provider_status_without_main_app_router_tree():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "relay",
            "RELAY_MESSAGE_ENDPOINT": "https://relay.example.com/messaging/relay-dispatch",
            "RELAY_MESSAGE_TOKEN": "secret",
        },
        clear=False,
    ):
        response = client.get("/messaging/provider-status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["provider"] == "relay"


def test_relay_app_relay_dispatch_forwards_to_target_provider():
    with patch.dict(
        "os.environ",
        {
            "RELAY_MESSAGE_TOKEN": "expected-token",
            "RELAY_TARGET_PROVIDER": "surem",
        },
        clear=False,
    ), patch(
        "web.message.backend.relay_runtime.MessagingService._dispatch_payload",
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
                "record_type": "SMS",
                "content": "hello",
            },
            headers={"Authorization": "Bearer expected-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["provider"] == "surem"
    _, kwargs = mock_dispatch.call_args
    assert kwargs["provider_name_override"] == "surem"
