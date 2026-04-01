import os
from typing import Any, Dict

from .base import BaseMessageProvider
from .mock_provider import MockMessageProvider
from .relay_provider import RelayMessageProvider
from .slack_notifier import SlackMessageProvider
from .surem_provider import SuremMessageProvider


class MessageProviderFactory:
    @staticmethod
    def is_vercel_environment() -> bool:
        return bool(os.getenv("VERCEL"))

    @staticmethod
    def render_service_name() -> str:
        return os.getenv("RENDER_SERVICE_NAME", "").strip()

    @staticmethod
    def is_render_environment() -> bool:
        return bool(MessageProviderFactory.render_service_name())

    @staticmethod
    def allow_message_send_on_render() -> bool:
        return os.getenv("ALLOW_MESSAGE_SEND_ON_RENDER", "").strip().lower() == "true"

    @staticmethod
    def render_delivery_blocked() -> bool:
        return MessageProviderFactory.is_render_environment() and not MessageProviderFactory.allow_message_send_on_render()

    @staticmethod
    def render_delivery_block_message() -> str:
        return "Message sending is disabled on this deployment. Contact the administrator."

    @staticmethod
    def get_provider_name() -> str:
        return os.getenv("MESSAGE_PROVIDER", "mock").strip().lower() or "mock"

    @staticmethod
    def get_provider_by_name(provider_name: str) -> BaseMessageProvider:
        normalized = (provider_name or "mock").strip().lower()
        if normalized == "surem":
            return SuremMessageProvider()
        if normalized == "slack":
            return SlackMessageProvider()
        if normalized == "relay":
            return RelayMessageProvider()
        return MockMessageProvider()

    @staticmethod
    def get_provider() -> BaseMessageProvider:
        return MessageProviderFactory.get_provider_by_name(MessageProviderFactory.get_provider_name())

    @staticmethod
    def get_provider_status() -> Dict[str, Any]:
        provider_name = MessageProviderFactory.get_provider_name()
        is_vercel = MessageProviderFactory.is_vercel_environment()
        render_service = MessageProviderFactory.render_service_name()
        return {
            "provider": provider_name,
            "environment": {
                "vercel": is_vercel,
                "render": bool(render_service),
                "render_service_name": render_service or None,
            },
            "delivery_policy": {
                "render_delivery_blocked": MessageProviderFactory.render_delivery_blocked(),
                "allow_message_send_on_render": MessageProviderFactory.allow_message_send_on_render(),
            },
            "slack": {
                "configured": bool(os.getenv("SLACK_MESSAGE_WEBHOOK_URL", "").strip()),
            },
            "relay": {
                "endpoint_configured": bool(os.getenv("RELAY_MESSAGE_ENDPOINT", "").strip()),
                "token_configured": bool(os.getenv("RELAY_MESSAGE_TOKEN", "").strip()),
                "target_provider": os.getenv("RELAY_TARGET_PROVIDER", "").strip() or "surem",
            },
            "surem": {
                "user_code_configured": bool(os.getenv("SUREM_USER_CODE", "").strip() or os.getenv("SUREM_AUTH_userCode", "").strip()),
                "secret_key_configured": bool(os.getenv("SUREM_SECRET_KEY", "").strip() or os.getenv("SUREM_AUTH_secretKey", "").strip()),
                "req_phone_configured": bool(os.getenv("SUREM_REQ_PHONE", "").strip() or os.getenv("SUREM_reqPhone", "").strip()),
                "force_to_number_configured": bool(os.getenv("SUREM_FORCE_TO_NUMBER", "").strip() or os.getenv("SUREM_TO", "").strip()),
            },
            "recommendation": (
                "Use relay when Vercel should hand message delivery to a protected runtime. "
                "Use Slack only for dev/test notification verification."
            ),
            "warnings": MessageProviderFactory._build_provider_warnings(provider_name, is_vercel, bool(render_service)),
        }

    @staticmethod
    def _build_provider_warnings(provider_name: str, is_vercel: bool, is_render: bool) -> list[str]:
        warnings: list[str] = []
        if is_render and MessageProviderFactory.render_delivery_blocked():
            warnings.append(MessageProviderFactory.render_delivery_block_message())
        if provider_name == "slack":
            warnings.append("Slack provider is for dev/test verification only. No carrier SMS/LMS/MMS delivery is attempted.")
        elif provider_name == "surem":
            warnings.append("SureM provider currently uses fixed-recipient relay-safe sends and supports SMS, LMS, and MMS when image requirements are satisfied.")
            if is_vercel:
                warnings.append("Prefer relay mode on Vercel when message delivery should be delegated to a protected runtime.")
        elif provider_name == "relay":
            warnings.append("Relay provider forwards delivery to a separate runtime. Keep the relay endpoint protected with RELAY_MESSAGE_TOKEN.")
        else:
            warnings.append("Mock provider does not contact any external delivery service.")
        return warnings
