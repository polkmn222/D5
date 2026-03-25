# Phase 87 Walkthrough

## Result

- The Lead title and `New` action now render inside the card header instead of the top strip, matching the requested lower placement.
- The list-view action area now uses a `Setup` button instead of the old gear entry.
- `Setup` opens a configuration panel where users can choose which Lead columns appear in the table, and the selection persists in the current browser.
- Users can reset the customized layout at any time from the same panel.

## Validation

- Backed up the touched Lead list template, list-view JS, list-view CSS, and focused test file under `.gemini/development/backups/phase87/` before editing.
- Verified the template renders successfully with a direct Jinja render after the layout changes.
- Test command used:
  - `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit/crm/leads/test_crud.py .gemini/development/test/unit/ui/shared/test_core_ui.py .gemini/development/test/unit/ui/tables/test_table_sorting_structure.py .gemini/development/test/unit/ui/shared/test_lead_list_view_controls.py -q`
