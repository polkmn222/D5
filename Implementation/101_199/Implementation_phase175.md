# Implementation Plan - Search Improvement (Phase 175)

This plan addresses search-related UI and functional improvements in both the Global Search and the AI Agent Table.

## Proposed Changes

### Global Search UI
#### [MODIFY] [search_results.html](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/search_results.html)
- Update the "View" button style to match the standard buttons found in list views.
- **Change**: Change `padding: 0.25rem 0.5rem; font-size: 0.75rem;` to `padding: 2px 8px; font-size: 0.75rem;` to unify the look.

### AI Agent Table Search
#### [MODIFY] [ai_agent.js](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/ui/frontend/static/js/ai_agent.js)
- Implement a debounced "Enter" or "Auto-search" for the table search box to trigger a backend "LIKE" search across all records instead of just the current page.
- **Change**: When the user presses Enter in the search input, ensure it correctly triggers `requestAgentSearch`.
- **Change**: Add a visual hint or support partial "LIKE" keywords for broader results.
- **Note**: The backend already supports `ILIKE` partial matching in `service.py`.

## Verification Plan

### Automated Tests
- No new backend tests required if the current `test_lead_join_phase174.py` and existing search tests cover the partial matching logic.
- I will verify `_apply_search_to_sql` in `service.py` handles Korean partial matching correctly if applicable.

### Manual Verification
- **None** (Per instructions: manual test is strictly forbidden)
