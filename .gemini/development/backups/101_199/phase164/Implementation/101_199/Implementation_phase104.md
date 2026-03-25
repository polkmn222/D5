# Phase 104 Implementation

## Changes

- Confirmed `Message` scope includes both `Send` (`/messages`) and `Template` (`/message_templates`); both remain under the messaging area.
- Added server-side pagination and row limiting for the slowest list pages: `/messages`, `/products`, and `/models`.
- Reduced server-side list-route overhead further by combining pagination with the earlier batch preloading changes.
- Added visible pagination controls to the Product, Model, and Message list-view templates.
- Added unit coverage for the new pagination UI rendering in Message, Product, and Model list views.

## Performance Results

- After restart and pagination:
  - `/messages/` about `1.375s`
  - `/products/` about `0.825s`
  - `/models` about `0.815s`
- This is a large improvement from the earlier live timings, especially for `/messages/`.

## Verification

- Ran `python -m py_compile .gemini/development/web/backend/app/api/routers/product_router.py .gemini/development/web/backend/app/api/routers/vehicle_spec_router.py .gemini/development/web/message/backend/routers/message_router.py`.
- Ran `pytest .gemini/development/test/unit/ui/shared/test_message_list_view_controls.py .gemini/development/test/unit/ui/shared/test_product_list_view_controls.py .gemini/development/test/unit/ui/shared/test_model_list_view_controls.py -q`.
- Ran `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit/crm/contacts/test_contacts.py .gemini/development/test/unit/crm/leads/test_crud.py .gemini/development/test/unit/ui/shared/test_core_ui.py .gemini/development/test/unit/ui/tables/test_table_sorting_structure.py .gemini/development/test/unit/ui/shared/test_lead_list_view_controls.py .gemini/development/test/unit/ui/shared/test_contact_list_view_controls.py .gemini/development/test/unit/ui/shared/test_opportunity_list_view_controls.py .gemini/development/test/unit/ui/shared/test_product_list_view_controls.py .gemini/development/test/unit/ui/shared/test_asset_list_view_controls.py .gemini/development/test/unit/ui/shared/test_brand_list_view_controls.py .gemini/development/test/unit/ui/shared/test_model_list_view_controls.py .gemini/development/test/unit/ui/shared/test_message_list_view_controls.py .gemini/development/test/unit/ui/shared/test_message_template_list_view_controls.py -q`.
- Result: `67 passed`.
