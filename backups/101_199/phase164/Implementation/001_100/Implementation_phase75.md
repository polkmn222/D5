# Phase 75 - Canonical `web/` Runtime Migration

## Goals
- Move the main web runtime into a single canonical `web/` container.
- Keep deployment and runtime behavior stable during the migration.
- Preserve compatibility while updating docs and tests to the new structure.

## Implemented Changes

### 1. Structural Migration
- Moved the active main runtime directories into `.gemini/development/web/`:
  - `backend/` -> `web/backend/`
  - `frontend/` -> `web/frontend/`
  - `app/static/uploads/` -> `web/app/static/uploads/`
- Added compatibility links at:
  - `.gemini/development/backend`
  - `.gemini/development/frontend`
  - `.gemini/development/app/static/uploads`

### 2. Runtime Path Updates
- `api/index.py` now imports `web.backend.app.main:app`.
- `render.yaml` now starts `uvicorn web.backend.app.main:app`.
- `web/backend/app/main.py` now mounts:
  - `/static` from `web/frontend/static`
  - `/static/uploads` from `web/app/static/uploads`
- `web/backend/app/core/templates.py` now resolves templates from `web/frontend/templates`.

### 3. Upload Path Updates
- Messaging image upload and template upload code now resolve canonical upload paths under `web/app/static/uploads`.
- Legacy relative paths continue to work through compatibility links, but the code now targets the canonical `web/` location.

### 4. Docs and Test Updates
- Updated active docs to reflect the canonical `web/` runtime.
- Updated path-sensitive tests to use `web/frontend/templates`.

## Files Changed
- `api/index.py`
- `render.yaml`
- `.gemini/development/web/backend/app/main.py`
- `.gemini/development/web/backend/app/core/templates.py`
- `.gemini/development/web/backend/app/api/messaging_router.py`
- `.gemini/development/web/backend/app/api/routers/message_template_router.py`
- `.gemini/development/docs/agent.md`
- `.gemini/development/docs/architecture.md`
- `.gemini/development/docs/deployment.md`
- `.gemini/development/docs/skill.md`
- `.gemini/development/docs/ui_standards.md`
- `.gemini/development/docs/blueprint.md`
- `.gemini/development/docs/SESSION_HANDOFF.md`
- `.gemini/development/test/unit/test_batch_edit_ui.py`
- `.gemini/development/test/unit/test_table_sorting_structure.py`
- `.gemini/development/test/docs/implementation_e2e_unit_testing.md`
- `.gemini/development/test/docs/walkthrough_e2e_unit_testing.md`

## Notes
- Antigravity MCP `sequential-thinking` was not available in the current toolchain, so the migration followed the docs-driven workflow directly.

## Backup
- `.gemini/development/backups/phase75/`
