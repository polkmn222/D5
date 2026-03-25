# Implementation Plan - Phase 178: Global Search UI Improvement

This phase focuses on improving the Global Search UI to be more consistent with the rest of the application and to follow a Salesforce-like design where results are grouped by object type. Additionally, the search logic will be refined to prioritize Name and Phone searches, excluding ID-based searches as per user requirements.

## Proposed Changes

### Backend: Search Logic Refinement
#### [MODIFY] [search_service.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/backend/app/services/search_service.py)
- Update `global_search` method to only search in Name and Phone fields for Leads and Contacts.
- Remove Email from the search criteria to align with the "Name or Phone only" requirement.
- Ensure other objects (Opportunity, Model, etc.) continue to search in their respective Name fields.

### Frontend: UI Enhancements
#### [MODIFY] [search_results.html](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/frontend/templates/search_results.html)
- **Two-Column Layout**: Update the results page to feature a sidebar on the left and results on the right.
- **Sidebar Navigation**:
    - "Top Results" (All) link to show global grouped results.
    - Individual object links (Leads, Contacts, etc.) with record counts.
    - Highlight active navigation state.
- **Dynamic Filtering**:
    - When an object is selected in the sidebar, show only that object's results.
- **Dynamic Columns**: Implement object-specific columns for each table, matching the "All" list view of that object.
- **Consistent Styling**: Ensure the sidebar and results follow Salesforce's neutral/premium aesthetic.

### Backend: Routing & Controller
#### [MODIFY] [dashboard_router.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/web/backend/app/api/routers/dashboard_router.py)
- Update the `global_search` route to pass grouped results to the template if necessary, or ensure the template can easily group the existing flat list.

## Backup and Safety
- Before making changes, the following files will be backed up to `backups/phase178/`:
    - `web/backend/app/services/search_service.py`
    - `web/frontend/templates/search_results.html`
    - `web/backend/app/api/routers/dashboard_router.py`

## Verification Plan

### Automated Tests
- Create a new unit test file `test/unit/search/test_search_logic_phase178.py` to verify:
    - Searching by Name returns correct results.
    - Searching by Phone returns correct results.
    - Searching by Email or ID does NOT return results (or is excluded from the primary logic).
    - Results are correctly grouped or group-able by type.
- Run tests using `pytest .gemini/development/test/unit/search/test_search_logic_phase178.py`.

### Manual Verification
- **NO MANUAL TESTING** as per user requirement. Verification will be done strictly through unit tests and code review.
