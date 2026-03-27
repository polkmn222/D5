from unittest.mock import patch

from fastapi.testclient import TestClient

from web.backend.app.main import app


client = TestClient(app)


def test_demo_availability_reports_unavailable_when_relay_endpoint_missing():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "relay",
            "RELAY_MESSAGE_TOKEN": "secret",
            "RELAY_MESSAGE_ENDPOINT": "",
        },
        clear=False,
    ):
        response = client.get("/messaging/demo-availability")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["reason"] == "relay_endpoint_not_configured"
    assert "Contact the administrator" in body["message"]


def test_demo_availability_reports_available_when_remote_health_succeeds():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "relay",
            "RELAY_MESSAGE_TOKEN": "secret",
            "RELAY_MESSAGE_ENDPOINT": "https://demo-bridge.example.com/messaging/relay-dispatch",
        },
        clear=False,
    ), patch(
        "web.message.backend.router._check_remote_demo_relay_health",
        return_value={
            "available": True,
            "message": "",
            "reason": None,
            "provider": "solapi",
            "mode": "relay",
        },
    ):
        response = client.get("/messaging/demo-availability")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["mode"] == "relay"
    assert body["provider"] == "solapi"


def test_demo_relay_health_rejects_invalid_token():
    with patch.dict(
        "os.environ",
        {
            "RELAY_MESSAGE_TOKEN": "expected-token",
            "RELAY_TARGET_PROVIDER": "solapi",
            "SOLAPI_API_KEY": "key",
            "SOLAPI_API_SECRET": "secret",
            "SOLAPI_SENDER_NUMBER": "01012341234",
        },
        clear=False,
    ):
        response = client.get(
            "/messaging/demo-relay-health",
            headers={"Authorization": "Bearer wrong-token"},
        )

    assert response.status_code == 403
    body = response.json()
    assert body["available"] is False
    assert body["reason"] == "invalid_relay_token"


def test_demo_relay_health_reports_missing_provider_env():
    with patch.dict(
        "os.environ",
        {
            "RELAY_MESSAGE_TOKEN": "expected-token",
            "RELAY_TARGET_PROVIDER": "solapi",
            "SOLAPI_API_KEY": "",
            "SOLAPI_API_SECRET": "",
            "SOLAPI_SENDER_NUMBER": "",
        },
        clear=False,
    ):
        response = client.get(
            "/messaging/demo-relay-health",
            headers={"Authorization": "Bearer expected-token"},
        )

    assert response.status_code == 503
    body = response.json()
    assert body["available"] is False
    assert body["reason"].startswith("missing_demo_provider_env:")


def test_demo_relay_health_reports_ready_when_local_target_provider_is_configured():
    with patch.dict(
        "os.environ",
        {
            "RELAY_MESSAGE_TOKEN": "expected-token",
            "RELAY_TARGET_PROVIDER": "solapi",
            "SOLAPI_API_KEY": "key",
            "SOLAPI_API_SECRET": "secret",
            "SOLAPI_SENDER_NUMBER": "01012341234",
        },
        clear=False,
    ):
        response = client.get(
            "/messaging/demo-relay-health",
            headers={"Authorization": "Bearer expected-token"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["provider"] == "solapi"
