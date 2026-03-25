# Phase 133 Implementation

## Changes

- Created `task/task_phase133.md` and backed up the edited source files plus a full JSON export of the active runtime data under `.gemini/development/backups/phase133/` before the destructive reset.
- Verified and updated `.gemini/development/web/backend/metadata.json` so the opportunity stage description and vehicle specification descriptions match the current schema and runtime usage more closely.
- Updated `.gemini/development/web/backend/app/api/routers/opportunity_router.py` so Opportunity detail pages expose the full stage sequence to the template and the inline batch-save endpoint now correctly maps renamed fields and lookup hidden refs (`Opportunity Name`, `Contact/Brand/Model/Product/Asset Hidden Ref`) while normalizing numeric edits.
- Updated `.gemini/development/web/frontend/templates/opportunities/detail_view.html` so `Stage` edits use a picklist, `Status` uses a picklist, `Close Date` uses a date input, `Probability` uses a numeric input, and stage changes now preview against the path bar through `syncOpportunityPathPreview(...)`.
- Hard-reset the active CRM records and regenerated 50 realistic linked records for each main object family using a deterministic premium automotive dataset. Final counts are:
  - `vehicle_specifications`: 50
  - `models`: 50
  - `products`: 50
  - `contacts`: 50
  - `leads`: 50
  - `attachments`: 50
  - `message_templates`: 50
  - `assets`: 50
  - `opportunities`: 50
  - `message_sends`: 50
- Cleared custom saved list-view rows during the reset so the app returns to built-in list views only.
- Stored the regenerated data counts in `.gemini/development/backups/phase133/data/regenerated_seed_summary.json` and the metadata/schema verification report in `.gemini/development/backups/phase133/data/metadata_db_verification.json`.

## Verification

- Ran `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit/ui/shared/test_core_ui.py .gemini/development/test/unit/ui/shared/test_opportunity_list_view_controls.py .gemini/development/test/unit/web/backend/test_opportunity_batch_save.py .gemini/development/test/unit/ui/shared/test_message_list_view_controls.py .gemini/development/test/unit/ui/shared/test_message_template_list_view_controls.py .gemini/development/test/unit/ui/shared/test_model_list_view_controls.py .gemini/development/test/unit/ui/shared/test_batch_save_logic.py .gemini/development/test/unit/messaging/templates/test_save.py -q`.
- Result: `64 passed`.
- Verified `metadata.json` against the live database schema; no metadata/schema drift remained after the update.
