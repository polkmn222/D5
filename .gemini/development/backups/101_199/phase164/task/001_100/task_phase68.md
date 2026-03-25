# Phase 68 Task

## Scope
- Replace direct messaging-service coupling with a provider abstraction.
- Support free dev/test channels with a safe default.

## Acceptance Criteria
- Messaging uses a provider factory.
- `MESSAGE_PROVIDER=mock` works as the default path.
- `slack` provider option exists behind the same interface as the default mock path.
- `MessageSend.provider_message_id` is populated from provider responses.
- Unit and regression tests pass.
