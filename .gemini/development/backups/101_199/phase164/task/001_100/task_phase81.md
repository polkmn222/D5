# Phase 81 Task

## Scope
- Separate the messaging feature into a dedicated `web/message/` subsystem.
- Move messaging-specific backend services/routers and frontend templates out of the general `web/backend` and `web/frontend` surfaces.
- Update imports, docs, and tests to the new canonical messaging paths.

## Acceptance Criteria
- Messaging runtime code lives under `.gemini/development/web/message/`.
- Main web app still includes messaging routes and templates correctly.
- Active docs mention the dedicated messaging subsystem.
- Focused and full unit suites pass.
