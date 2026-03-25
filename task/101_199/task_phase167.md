# Task Phase 167: AI Agent Lead UX and Data Table UI Enhancement

## Objective
1. Improve the AI Agent conversation flow by naturally transitioning to the "lead open" (view) state after lead creation/edit.
2. Enhance the data table UI with icons for "Select All" and "Clear All".
3. Change the color of the "Edit" button in the data table.
4. Reduce pagination from 50 to 30 records per page.

## Detailed Tasks
### 1. Lead UX Transition
- **File:** `.gemini/development/ai_agent/backend/service.py`
- **Change:** 
    - In `_execute_intent` for `UPDATE` intent of `lead` object:
        - Change `mode="edit"` to `mode="view"` when calling `_build_lead_chat_card`.
        - Update the success message to: `Success! I've updated the Lead {record_id} and opened the refreshed card below.`
    - (Optional) Verify `CREATE` intent already uses `mode="view"`.

### 2. Data Table UI - Icons
- **File:** `.gemini/development/ai_agent/frontend/static/js/ai_agent.js`
- **Change:**
    - In `renderAgentResultsMarkup`:
        - Update "Select All" button: `<button class="control-btn" onclick="selectAllAgentRows(this, '${objectType}')"><span style="margin-right:4px;">☑</span>Select All</button>`
        - Update "Clear All" button: `<button class="control-btn" onclick="clearAllAgentRows(this, '${objectType}')"><span style="margin-right:4px;">☒</span>Clear All</button>`

### 3. Edit Button Color
- **File:** `.gemini/development/ai_agent/frontend/static/js/ai_agent.js`
- **Change:** 
    - In `renderAgentResultsMarkup`: Change the "Edit" button class from `control-btn-action` to `control-btn-edit`.
- **File:** `.gemini/development/ai_agent/frontend/static/css/ai_agent.css`
- **Change:** 
    - Define `.control-btn-edit` and `.control-btn-edit:hover` with a green color scheme.

### 4. Pagination Reduction
- **File:** `.gemini/development/ai_agent/frontend/static/js/ai_agent.js`
- **Change:** 
    - Change `per_page: 50` to `30`.
    - Change any logic that checks for `results.length > 50` to `30`.
- **File:** `.gemini/development/ai_agent/backend/service.py`
- **Change:** 
    - Change default `per_page` in `_execute_intent` to `30`.
    - Change default `per_page` in `_sanitize_pagination` to `30`.

## Verification & Testing
- **Unit Tests:**
    - Run `pytest .gemini/development/test/unit/ai_agent/backend/test_lead_flow_consistency.py`.
    - Add/update a test case to verify `per_page` default is 30.
