# Web Message Guide

## Scope

- This folder owns the messaging subsystem.
- Backend code lives in `backend/`.
- Messaging-specific templates live in `frontend/`.

## Canonical Docs

- Primary rules live in `/.gemini/development/docs/skill.md`.
- Runtime structure lives in `/.gemini/development/docs/architecture.md`.
- Messaging and deployment behavior lives in `/.gemini/development/docs/agent.md` and `/.gemini/development/docs/deployment.md`.
- Testing rules live in `/.gemini/development/docs/testing/`.

## Entrypoints

- `backend/router.py`: top-level messaging routes and service wiring.
- `backend/routers/`: feature routers such as template and send flows.
- `frontend/templates/message_templates/`: template UI.
- `frontend/templates/messages/`: message-send detail and list UI.

## Current Rules

- Messaging pages do not live under `web/frontend/`; they live under `web/message/frontend/`.
- `message_templates/detail_view.html` is the editable messaging detail surface.
- `messages/detail_view.html` uses object-level actions and should not be treated like a shared inline-pencil detail page.
- SMS templates and SMS sends do not use a subject.
- Provider behavior depends on `MESSAGE_PROVIDER`.

## Attachment Notes

- Template and upload guidance allows JPG images up to 500KB.
- Real Solapi MMS sends are stricter and require JPG images at or under 200KB.
- Keep upload-path rules and provider send-path rules distinct in docs and tests.

## Common Gotchas

- Do not point messaging tests at `web/frontend/templates/messages/...` or `web/frontend/templates/message_templates/...`.
- Keep direct-call router tests aligned with the current function signatures in `backend/router.py` and `backend/routers/`.
- Verify provider-specific behavior before changing shared CRM services for a messaging-only need.

## Tests

- Messaging unit tests live under `/.gemini/development/test/unit/messaging/`.
- Shared UI tests that touch messaging templates live under `/.gemini/development/test/unit/ui/shared/`.
