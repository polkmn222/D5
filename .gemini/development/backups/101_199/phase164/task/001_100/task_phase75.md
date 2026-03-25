# Phase 75 Task

## Scope
- Migrate the main web runtime under `.gemini/development/web/`.
- Move `backend/`, `frontend/`, and `app/static/uploads/` into the new `web/` container.
- Update code, docs, deployment paths, and tests to use the new canonical structure.
- Preserve runtime compatibility during migration.

## Acceptance Criteria
- Canonical web runtime lives under `.gemini/development/web/`.
- Main app still boots through Vercel and Render entry paths.
- Shared templates/static/uploads resolve correctly after the move.
- Active docs reflect the new structure.
- Focused and regression tests pass.
