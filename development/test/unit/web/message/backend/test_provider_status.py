from unittest.mock import patch

from web.message.backend.services.message_providers.factory import MessageProviderFactory


def test_provider_status_warns_for_surem_on_vercel():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "surem",
            "VERCEL": "1",
            "SUREM_USER_CODE": "user-code",
            "SUREM_SECRET_KEY": "secret",
            "SUREM_REQ_PHONE": "15884640",
            "SUREM_FORCE_TO_NUMBER": "01012341234",
        },
        clear=False,
    ):
        status = MessageProviderFactory.get_provider_status()

    assert status["provider"] == "surem"
    assert status["environment"]["vercel"] is True
    assert status["surem"]["user_code_configured"] is True
    assert any("Prefer relay mode on Vercel" in warning for warning in status["warnings"])


def test_provider_status_marks_slack_as_dev_test_only():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "slack",
            "SLACK_MESSAGE_WEBHOOK_URL": "https://hooks.slack.com/services/test",
        },
        clear=False,
    ):
        status = MessageProviderFactory.get_provider_status()

    assert status["provider"] == "slack"
    assert status["slack"]["configured"] is True
    assert any("dev/test verification only" in warning for warning in status["warnings"])


def test_provider_status_reports_relay_configuration():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "relay",
            "RELAY_MESSAGE_ENDPOINT": "https://relay.example.com/messaging/relay-dispatch",
            "RELAY_MESSAGE_TOKEN": "secret",
        },
        clear=False,
    ):
        status = MessageProviderFactory.get_provider_status()

    assert status["provider"] == "relay"
    assert status["relay"]["endpoint_configured"] is True
    assert status["relay"]["token_configured"] is True
    assert status["relay"]["target_provider"] == "surem"
    assert any("separate runtime" in warning for warning in status["warnings"])


def test_provider_status_reports_render_delivery_block_by_default():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "relay",
            "RENDER_SERVICE_NAME": "d5-app",
        },
        clear=False,
    ):
        status = MessageProviderFactory.get_provider_status()

    assert status["environment"]["render"] is True
    assert status["delivery_policy"]["render_delivery_blocked"] is True
    assert any("Contact the administrator" in warning for warning in status["warnings"])


def test_provider_status_reports_surem_configuration():
    with patch.dict(
        "os.environ",
        {
            "MESSAGE_PROVIDER": "surem",
            "SUREM_USER_CODE": "user-code",
            "SUREM_SECRET_KEY": "secret-key",
            "SUREM_REQ_PHONE": "15884640",
            "SUREM_FORCE_TO_NUMBER": "01000000000",
        },
        clear=False,
    ):
        status = MessageProviderFactory.get_provider_status()

    assert status["provider"] == "surem"
    assert status["surem"]["user_code_configured"] is True
    assert status["surem"]["secret_key_configured"] is True
    assert status["surem"]["req_phone_configured"] is True
    assert status["surem"]["force_to_number_configured"] is True
    assert any("supports SMS, LMS, and MMS" in warning for warning in status["warnings"])


def test_provider_status_defaults_to_mock():
    with patch.dict("os.environ", {}, clear=True):
        status = MessageProviderFactory.get_provider_status()

    assert status["provider"] == "mock"
    assert any("does not contact any external delivery service" in warning for warning in status["warnings"])
