# Phase 81 - Dedicated `web/message/` Subsystem

## Goals
- Split the messaging feature into its own canonical runtime subtree under `web/message/`.
- Reduce coupling between general CRM runtime code and messaging-specific backend/frontend behavior.

## Implemented Changes

### 1. New Canonical Messaging Structure
- Added the following canonical messaging paths:
  - `.gemini/development/web/message/backend/`
  - `.gemini/development/web/message/frontend/`
- Moved messaging-specific files into the new subsystem:
  - backend router: `web/message/backend/router.py`
  - backend routers: `web/message/backend/routers/`
  - backend services: `web/message/backend/services/`
  - provider adapters: `web/message/backend/services/message_providers/`
  - templates: `web/message/frontend/templates/`

### 2. Runtime Integration
- `web/backend/app/api/api_router.py` now includes messaging routers from `web.message.backend`.
- `web/backend/app/core/templates.py` now loads template search paths from `web/message/frontend/templates/`.
- Shared CRM routes and AI Agent integrations now import messaging services from `web.message.backend.services`.

### 3. Docs and Tests
- Updated active docs to mention `web/message/` as a dedicated subsystem.
- Updated messaging tests and UI path-sensitive tests to reference canonical `web/message/...` paths.
- Added package markers and retained full test compatibility.

## Files Changed
- `.gemini/development/web/backend/app/api/api_router.py`
- `.gemini/development/web/backend/app/api/form_router.py`
- `.gemini/development/web/backend/app/api/routers/utility_router.py`
- `.gemini/development/web/backend/app/core/templates.py`
- `.gemini/development/web/message/backend/router.py`
- `.gemini/development/web/message/backend/routers/message_router.py`
- `.gemini/development/web/message/backend/routers/message_template_router.py`
- `.gemini/development/web/message/backend/services/messaging_service.py`
- `.gemini/development/web/message/backend/services/message_service.py`
- `.gemini/development/web/message/backend/services/message_template_service.py`
- `.gemini/development/web/message/backend/services/message_providers/*`
- `.gemini/development/web/message/frontend/templates/send_message.html`
- `.gemini/development/web/message/frontend/templates/messages/*`
- `.gemini/development/web/message/frontend/templates/message_templates/*`
- `.gemini/development/ai_agent/backend/service.py`
- `.gemini/development/docs/agent.md`
- `.gemini/development/docs/architecture.md`
- `.gemini/development/docs/deployment.md`
- `.gemini/development/docs/skill.md`
- `.gemini/development/docs/blueprint.md`
- `.gemini/development/docs/SESSION_HANDOFF.md`
- `.gemini/development/test/unit/...` messaging and UI references

## Verification
- `python -c "from web.backend.app.main import app; from web.message.backend.router import router; print(app.title, bool(router))"`
- Focused suite: `47 passed`
- Full unit suite: `205 passed, 4 skipped`

## Backup
- `.gemini/development/backups/phase81/`
