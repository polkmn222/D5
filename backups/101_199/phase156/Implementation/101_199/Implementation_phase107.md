# Phase 107 Implementation

## Changes

- Extended the shared modal AJAX flow in `web/frontend/templates/base.html` so `Save & New` now works through the same fetch-based submit path.
- Added a reusable global loading overlay in `web/frontend/templates/base.html` for user-driven navigation and CRUD-style actions.
- Wired the loading state into modal opening, JSON CRUD actions, modal form saves, link navigation, and standard non-AJAX form submits.
- Explicitly excluded AI recommendation controls from the global loading overlay logic.
- Updated the shared modal templates and the custom Lead modal so `Save & New` submits through the shared AJAX handler using `data-submit-mode="save-new"`.

## Verification

- Ran `pytest .gemini/development/test/unit/ui/shared/test_core_ui.py -q`.
- Ran `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit/crm/contacts/test_contacts.py .gemini/development/test/unit/crm/leads/test_crud.py .gemini/development/test/unit/ui/shared/test_core_ui.py .gemini/development/test/unit/ui/tables/test_table_sorting_structure.py .gemini/development/test/unit/ui/shared/test_lead_list_view_controls.py .gemini/development/test/unit/ui/shared/test_contact_list_view_controls.py .gemini/development/test/unit/ui/shared/test_opportunity_list_view_controls.py .gemini/development/test/unit/ui/shared/test_product_list_view_controls.py .gemini/development/test/unit/ui/shared/test_asset_list_view_controls.py .gemini/development/test/unit/ui/shared/test_brand_list_view_controls.py .gemini/development/test/unit/ui/shared/test_model_list_view_controls.py .gemini/development/test/unit/ui/shared/test_message_list_view_controls.py .gemini/development/test/unit/ui/shared/test_message_template_list_view_controls.py -q`.
- Result: `69 passed`.
