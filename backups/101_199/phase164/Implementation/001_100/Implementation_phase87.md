# Phase 87 Implementation

## Changes

- Reworked `web/frontend/templates/leads/list_view.html` so the Lead page title and primary action buttons now sit inside the list-view card instead of the top page strip.
- Updated the Lead list header layout to match the requested positioning, with the title block on the left and `New` / `Delete` actions aligned on the right inside the card.
- Replaced the broken gear dropdown with a `Setup` button that opens a list-view customization panel.
- Added client-side Lead list customization in `web/frontend/static/js/list_views.js` so users can choose which columns appear, save that layout in local storage, and reset it later.
- Expanded `web/frontend/static/css/list_views.css` to support the moved header, setup panel, and responsive layout.
- Updated `test/unit/ui/shared/test_lead_list_view_controls.py` with regression coverage for the new Setup UI and customization assets.

## Docs Referenced

- Used the project guidance in `.gemini/development/docs/agent.md`, `.gemini/development/docs/workflow.md`, `.gemini/development/docs/spec.md`, `.gemini/development/docs/blueprint.md`, and the testing docs under `.gemini/development/docs/testing/`.
- Antigravity MCP `sequential-thinking` is not exposed in the current toolchain, so the documented fallback workflow was used.

## Verification

- Rendered `leads/list_view.html` directly with minimal context to confirm the updated page still renders correctly.
- Ran: `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit/crm/leads/test_crud.py .gemini/development/test/unit/ui/shared/test_core_ui.py .gemini/development/test/unit/ui/tables/test_table_sorting_structure.py .gemini/development/test/unit/ui/shared/test_lead_list_view_controls.py -q`
- Result: `9 passed`.
