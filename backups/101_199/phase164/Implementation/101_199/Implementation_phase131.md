# Phase 131 Implementation

## Changes

- Created `task/task_phase131.md` and stored code plus pre-change lookup snapshots under `.gemini/development/backups/phase131/` before editing runtime code and data.
- Updated `.gemini/development/web/frontend/static/css/list_views.css` so list-view tables render on a white surface consistently, fixing the Send list table background mismatch.
- Updated `.gemini/development/web/message/frontend/templates/messages/list_view.html` so the Send row action uses the same compact button treatment as the other object list views.
- Added `messages` support to `.gemini/development/web/backend/app/api/routers/utility_router.py` so message batch-save requests are no longer rejected as an unsupported object type.
- Reworked `.gemini/development/web/message/frontend/templates/messages/detail_view.html` into a read-only detail surface with a proper `Content` section, removing the accidental editable-message UX that produced the unsupported save path.
- Kept the Send/Template related chain working by preserving the related-card routes from phase130 and verifying the simplified related-mode Template list in `.gemini/development/web/message/backend/routers/message_template_router.py`.
- Backfilled missing lookup data directly in the runtime database for the connected CRM graph used by Related tabs. Filled counts were:
  - `models.brand`: 4
  - `products.model`: 11
  - `products.brand`: 11
  - `leads.brand`: 127
  - `leads.model`: 135
  - `leads.product`: 134
  - `assets.contact`: 23
  - `assets.product`: 21
  - `assets.brand`: 32
  - `assets.model`: 32
  - `opportunities.contact`: 49
  - `opportunities.product`: 222
  - `opportunities.brand`: 222
  - `opportunities.model`: 119
  - `opportunities.asset`: 297
  - `message_sends.contact`: 16
  - `message_sends.template`: 260
- Left Contact records unchanged because they do not expose direct CRM lookup fields, left top-level Brand `parent` blank where appropriate, and left Template attachment lookups unchanged because they are not required for CRM related navigation.
- Saved the post-backfill summary to `.gemini/development/backups/phase131/data/lookup_backfill_after.json`.

## Verification

- Ran `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit/ui/shared/test_core_ui.py .gemini/development/test/unit/ui/shared/test_message_list_view_controls.py .gemini/development/test/unit/ui/shared/test_message_template_list_view_controls.py .gemini/development/test/unit/ui/shared/test_model_list_view_controls.py .gemini/development/test/unit/ui/shared/test_batch_save_logic.py .gemini/development/test/unit/messaging/templates/test_save.py -q`.
- Result: `52 passed`.
