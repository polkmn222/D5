import os

from .base import BaseMessageProvider
from .mock_provider import MockMessageProvider
from .slack_provider import SlackMessageProvider
from .solapi_provider import SolapiMessageProvider


class MessageProviderFactory:
    @staticmethod
    def get_provider() -> BaseMessageProvider:
        provider_name = os.getenv("MESSAGE_PROVIDER", "mock").strip().lower()
        if provider_name == "solapi":
            return SolapiMessageProvider()
        if provider_name == "slack":
            return SlackMessageProvider()
        return MockMessageProvider()
