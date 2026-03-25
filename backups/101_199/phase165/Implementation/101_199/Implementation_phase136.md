# Phase 136 Implementation

## Changes

- Re-read the active docs after the user callout, including the updated workflow, UI, spec, and testing guidance under `.gemini/development/docs/` and `.gemini/development/docs/testing/`, then used the next fully unused phase number (`136`) because `phase135` artifacts already existed.
- Added `.gemini/development/web/backend/app/services/record_delete_service.py` to centralize hard-delete behavior and related-record cleanup for Contacts, Leads, Opportunities, Assets, Products, Models, Brands, Messages, and Message Templates.
- Switched user-facing delete flows from soft delete to hard delete by updating the service layer: `ContactService`, `LeadService`, `OpportunityService`, `AssetService`, `ProductService`, `ModelService`, `VehicleSpecService`, `MessageService`, and `MessageTemplateService` now route deletions through hard-delete or cascade-delete behavior instead of setting `deleted_at`.
- Hardened `.gemini/development/web/backend/app/services/base_service.py` so foreign-key updates validate referenced ids, explicit blank lookup clears normalize to `NULL`, and create/update paths reject invalid deleted-or-missing lookup ids before the database throws raw FK errors.
- Hardened `.gemini/development/web/backend/app/api/routers/utility_router.py` so shared inline-save and batch-save flows map lookup hidden refs consistently, preserve explicit lookup clears through `_force_null_fields`, and filter lookup search results to active rows only.
- Added a new `/lookups/recent` endpoint and updated `.gemini/development/web/frontend/static/js/lookup.js` so recent lookup chips are revalidated against the server before rendering, stale deleted records are removed from local storage, and lookup type aliases share the same recent cache bucket.
- Removed the delete undo affordance from `.gemini/development/web/frontend/templates/base.html` because hard delete is now final and should not advertise a restore path.
- Updated object-specific batch-save handling where needed, especially `lead_router.py` and `opportunity_router.py`, so lookup clears save safely as `NULL` instead of invalid empty-string FK values.
- Purged historical soft-deleted rows from the runtime database and removed stale deleted records that could still leak into lookup flows. The purge summary is stored at `.gemini/development/backups/phase136/data/purge_soft_deleted_summary.json`.
- Verified lookup integrity after the purge; the report at `.gemini/development/backups/phase136/data/lookup_integrity_after_purge.json` shows zero active records pointing to missing lookup targets.

## Validation

- Ran `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit/crm/shared/test_deletion_integrity.py .gemini/development/test/unit/search/test_lookup_search.py .gemini/development/test/unit/crm/contacts/test_contacts.py .gemini/development/test/unit/crm/leads/test_crud.py .gemini/development/test/unit/ui/shared/test_batch_save_logic.py .gemini/development/test/unit/web/backend/test_opportunity_batch_save.py .gemini/development/test/unit/ai_agent/backend/test_messaging_crud.py .gemini/development/test/unit/ai_agent/backend/test_opp_contact_crud.py .gemini/development/test/unit/ai_agent/backend/test_comprehensive_crud.py -q`.
- Result: `25 passed`.
- Ran `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit/ui/shared/test_core_ui.py .gemini/development/test/unit/ui/shared/test_message_list_view_controls.py .gemini/development/test/unit/ui/shared/test_message_template_list_view_controls.py .gemini/development/test/unit/ui/shared/test_model_list_view_controls.py .gemini/development/test/unit/ui/shared/test_opportunity_list_view_controls.py .gemini/development/test/unit/ui/shared/test_batch_save_logic.py .gemini/development/test/unit/search/test_lookup_search.py .gemini/development/test/unit/crm/shared/test_deletion_integrity.py .gemini/development/test/unit/web/backend/test_opportunity_batch_save.py .gemini/development/test/unit/messaging/templates/test_save.py -q`.
- Result: `71 passed`.
