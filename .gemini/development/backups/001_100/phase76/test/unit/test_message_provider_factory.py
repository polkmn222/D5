from unittest.mock import patch

from web.backend.app.services.message_providers.factory import MessageProviderFactory
from web.backend.app.services.message_providers.mock_provider import MockMessageProvider
from web.backend.app.services.message_providers.slack_provider import SlackMessageProvider


def test_message_provider_factory_defaults_to_mock():
    with patch("os.getenv", return_value=""):
        provider = MessageProviderFactory.get_provider()

    assert isinstance(provider, MockMessageProvider)


def test_message_provider_factory_returns_slack_provider():
    with patch("os.getenv", return_value="slack"):
        provider = MessageProviderFactory.get_provider()

    assert isinstance(provider, SlackMessageProvider)
