# Phase 76 - Canonical Web Imports, Test Realignment, and Compatibility Removal

## Goals
- Complete the migration from legacy main-web paths to canonical `web/` runtime paths.
- Remove temporary compatibility links after active code and tests are updated.
- Validate the entire unit test suite against the canonical `web/` structure.

## Implemented Changes

### 1. Canonical Import Migration
- Updated active runtime code and AI agent integrations to reference `web.backend.app...` where the main web runtime is imported directly.
- Updated path-sensitive tests and docs to reference `web/frontend/...` and `web/backend/...`.

### 2. Compatibility Removal
- Removed the temporary compatibility symlinks for:
  - `.gemini/development/backend`
  - `.gemini/development/frontend`
  - `.gemini/development/app/static/uploads`
- Verified that `web.backend.app.main:app` still imports and boots successfully without them.

### 3. Test Packaging Fix
- Added `__init__.py` package markers under `test/unit/...` subtrees to prevent basename collisions during full test discovery.

### 4. Upload and Template Path Stabilization
- Ensured template upload and message image upload paths resolve from the canonical `web/app/static/uploads` location.

## Verification
- `python -c "from web.backend.app.main import app; print(app.title)"` -> `AI Ready CRM`
- `pytest test/unit/test_batch_edit_ui.py test/unit/test_table_sorting_structure.py test/unit/test_send_message_assets.py test/unit/test_messaging_router_upload_validation.py` -> passed
- `pytest test/unit` -> `208 passed`

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
- `.gemini/development/test/...` package markers and path-sensitive tests

## Notes
- Antigravity MCP `sequential-thinking` was not available in the current toolchain, so execution followed the required docs-driven workflow directly.

## Backup
- `.gemini/development/backups/phase76/`
