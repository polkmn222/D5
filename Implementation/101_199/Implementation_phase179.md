# Phase 179: Global Search UI Enhancements

Redesign the search results interaction by making record names clickable and adding direct Edit/Delete actions.

## Proposed Changes

### Frontend
#### [MODIFY] [search_results.html](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/search_results.html)
- Update "NAME" column to wrap record names in `<a>` tags linking to the record detail page.
- Replace the "View" button in the "ACTION" column with "Edit" and "Delete" buttons.
- Implement `onclick` handlers for "Edit" (calling `openModal`) and "Delete" (calling `confirmDelete`).
- Ensure consistent styling for the new buttons using Salesforce-like design patterns.

## Verification Plan

### Automated Tests
- Create/Update a rendering test script to verify that:
  - The "NAME" column contains a link with the correct `href`.
  - The "ACTION" column contains buttons with the expected `onclick` handlers.
- Run existing unit tests in `test_search_logic_phase178.py` to ensure core logic remains stable.

### Manual Verification
- N/A (Forbidden by user).
