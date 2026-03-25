# Implementation Plan - AI Agent Lead CRUD Enhancement (Phase 176)

This plan addresses the reported issue where Lead Create, Edit, and Delete functions in the AI Agent do not work correctly for the actual objects. We will align the AI Agent's Lead CRUD functionality with the web folder's implementation while ensuring a seamless user experience within the chat.

## Objective
- Ensure Lead **Create**, **Edit**, and **Delete** actions in the AI Agent correctly update the database.
- Streamline the user experience by reducing double-confirmation loops.
- Improve the reliability of inline forms and chat cards for Lead management.

## Key Files & Context
- **Backend Service**: `ai_agent/ui/backend/service.py` (Main intent logic)
- **Frontend Logic**: `ai_agent/ui/frontend/static/js/ai_agent.js` (Form wiring and response handling)
- **Lead Service**: `web/backend/app/services/lead_service.py` (Underlying CRUD logic)
- **Lead Router**: `web/backend/app/api/routers/lead_router.py` (Web endpoint reference)
- **Form Router**: `web/backend/app/api/form_router.py` (Modal form delivery)

## Proposed Changes

### 1. Refine Intent Handling in `AiAgentService`
#### [MODIFY] [ai_agent/ui/backend/service.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/ui/backend/service.py)
- **Streamline DELETE**: If the query is an explicit `Delete {object} {record_id}` from a trusted UI action, skip the second confirmation prompt and proceed with the deletion.
- **Robustness for CREATE/UPDATE**:
  - Ensure `_execute_intent` for `CREATE` and `UPDATE` correctly returns a failure message if `LeadService` returns `None`.
  - Add more explicit logging to track if the service call fails due to validation errors.
  - Refine `_detect_manage_mode` to be more robust regarding Korean language tokens.

### 2. Audit and Fix Frontend Form Wiring
#### [MODIFY] [ai_agent/ui/frontend/static/js/ai_agent.js](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/ui/frontend/static/js/ai_agent.js)
- **Ensure Correct POST Target**: Verify that `wireAgentInlineForm` correctly identifies the form's `action` attribute from `sf_form_modal.html`.
- **Handle Redirects Gracefully**: Ensure that after a successful form save (redirect), the chat correctly shows the success message and refreshes the lead's state in the conversation.
- **Fix "Edit" / "Delete" Buttons**: Ensure the buttons on the lead card correctly trigger the `Manage` flows in the backend.

### 3. Lead CRUD Service Integration (Optional if needed)
- If the current `sf_form_modal.html` is too complex for chat embedding, I will create a simpler version `ai_agent_lead_form.html` in `ai_agent/ui/frontend/templates/` that is specifically optimized for the AI Agent.

## Implementation Steps

### Step 1: Research & Reproduction
- Create comprehensive unit tests in `test/unit/ai_agent/backend/test_lead_crud_logic_phase176.py` that simulate real Lead CRUD scenarios without mocks where possible (or with more realistic mocks).
- Verify the current `CREATE`/`UPDATE`/`DELETE` intents via the tests.

### Step 2: Backend Logic Updates
- Modify `AiAgentService._resolve_delete_confirmation` to support immediate deletion for explicit requests.
- Ensure `_execute_intent` correctly handles service-layer failures.

### Step 3: Frontend Enhancement
- Update `ai_agent.js` to improve form wiring and error reporting.
- Ensure `triggerSnapshotDelete` and `triggerSelectionEdit` are perfectly synced with the backend logic.

### Step 4: Verification
- Run all related unit tests (`pytest test/unit/ai_agent/backend/test_lead_crud_logic*`).
- Confirm that the Lead cards now correctly reflect the state after Create/Update/Delete.

## Verification & Testing
### Automated Tests
- `pytest test/unit/ai_agent/backend/test_lead_crud_logic_phase176.py`
- `pytest test/unit/ai_agent/backend/test_lead_crud_logic_phase171.py` (Ensure no regressions)

### Manual Verification
- **None** (Per instructions)
