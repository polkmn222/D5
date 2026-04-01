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


def test_demo_availability_reports_render_delivery_block():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "relay",
            "RENDER_SERVICE_NAME": "d5-app",
            "RELAY_MESSAGE_TOKEN": "secret",
            "RELAY_MESSAGE_ENDPOINT": "https://demo-bridge.example.com/messaging/relay-dispatch",
        },
        clear=False,
    ):
        response = client.get("/messaging/demo-availability")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["reason"] == "render_delivery_blocked"


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
        "web.message.backend.relay_runtime._check_remote_demo_relay_health",
        return_value={
            "available": True,
            "message": "",
            "reason": None,
            "provider": "surem",
            "mode": "relay",
        },
    ):
        response = client.get("/messaging/demo-availability")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["mode"] == "relay"
    assert body["provider"] == "surem"


def test_demo_availability_uses_local_readiness_when_self_relay_endpoint_matches_request_host():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "relay",
            "RELAY_MESSAGE_TOKEN": "secret",
            "RELAY_MESSAGE_ENDPOINT": "http://testserver/messaging/relay-dispatch",
            "RELAY_TARGET_PROVIDER": "surem",
            "SUREM_AUTH_userCode": "user",
            "SUREM_AUTH_secretKey": "secret",
            "SUREM_reqPhone": "15884640",
            "SUREM_TO": "01000000000",
        },
        clear=False,
    ), patch(
        "web.message.backend.relay_runtime._check_remote_demo_relay_health",
        side_effect=AssertionError("self-relay should not perform remote health probe"),
    ):
        response = client.get("/messaging/demo-availability")

    assert response.status_code == 200
    body = response.json()
    assert body["available"] is True
    assert body["mode"] == "relay"
    assert body["provider"] == "surem"


def test_demo_relay_health_rejects_invalid_token():
    with patch.dict(
        "os.environ",
        {
            "RELAY_MESSAGE_TOKEN": "expected-token",
            "RELAY_TARGET_PROVIDER": "surem",
            "SUREM_AUTH_userCode": "user",
            "SUREM_AUTH_secretKey": "secret",
            "SUREM_reqPhone": "15884640",
            "SUREM_TO": "01000000000",
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
            "RELAY_TARGET_PROVIDER": "surem",
            "SUREM_AUTH_userCode": "",
            "SUREM_AUTH_secretKey": "",
            "SUREM_reqPhone": "",
            "SUREM_TO": "",
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
            "RELAY_TARGET_PROVIDER": "surem",
            "SUREM_AUTH_userCode": "user",
            "SUREM_AUTH_secretKey": "secret",
            "SUREM_reqPhone": "15884640",
            "SUREM_TO": "01000000000",
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
    assert body["provider"] == "surem"
