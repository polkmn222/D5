# Implementation Plan - AI Agent Lead CRUD Implementation (Phase 177)

This plan focuses on making the **Create**, **Edit**, and **Delete** functionality for Leads fully operational within the AI Agent on the Home tab. We will ensure that these actions correctly persist to the actual Lead objects in the database by leveraging the existing `LeadService` or creating a dedicated AI Agent UI layer for these operations.

## Objective
- Enable Lead **Create** functionality via natural language or inline forms in the AI Agent.
- Enable Lead **Edit** (Update) functionality via natural language or inline forms in the AI Agent.
- Enable Lead **Delete** functionality with immediate feedback in the AI Agent.
- Ensure all actions are persisted correctly to the PostgreSQL database.

## Key Files & Context
- **AI Agent Backend**: `.gemini/development/ai_agent/ui/backend/service.py` (Intent and Service coordination)
- **AI Agent Frontend**: `.gemini/development/ai_agent/ui/frontend/static/js/ai_agent.js` (Form wiring and UI updates)
- **Lead Service**: `.gemini/development/web/backend/app/services/lead_service.py` (Core CRUD logic)
- **Database Models**: `.gemini/development/db/models.py` (Lead entity definition)
- **Form Router**: `.gemini/development/web/backend/app/api/form_router.py` (Modal form delivery)

## Proposed Changes

### 1. Robust Backend Intent Execution
#### [MODIFY] [ai_agent/ui/backend/service.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/ui/backend/service.py)
- **Refine `_execute_intent` for CREATE/UPDATE**:
    - Ensure `LeadService.create_lead` and `LeadService.update_lead` are called with the correctly extracted and cleaned data.
    - Implement robust handling for `None` results (e.g., validation failures) to prevent crashes and provide helpful feedback.
    - Ensure `redirect_url` and `record_id` are correctly returned to the frontend to trigger UI updates.
- **Streamline DELETE**:
    - If the user provides an explicit `Delete lead {id}` command (e.g., clicking a 'Delete' button on a chat card), bypass the double-confirmation prompt for a smoother experience.
- **Improve Field Extraction**:
    - Enhance `_extract_lead_update_fields_from_text` to capture Korean field names and values with spaces (e.g., "브랜드는 현대", "상품명은 그랜저 하이브리드") using non-greedy regex.

### 2. Frontend Form Wiring and Redirect Handling
#### [MODIFY] [ai_agent/ui/frontend/static/js/ai_agent.js](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/ui/frontend/static/js/ai_agent.js)
- **Audit `wireAgentInlineForm`**:
    - Ensure that forms submitted within the AI Agent chat correctly POST to the intended endpoints (`/leads` or `/leads/{id}`).
    - Verify that the "Save" and "Save & New" buttons work as expected, correctly handling the `redirected` response.
- **Post-Action UI Refresh**:
    - After a successful Lead action (Create/Edit/Delete), ensure the chat interface correctly reflects the change (e.g., showing a success message or an updated record card).
    - Ensure `deleted_ids` from the backend are handled to remove the deleted lead from any visible tables.

### 3. Verification & Testing
- **New Unit Test**: Create `.gemini/development/test/unit/ai_agent/backend/test_lead_crud_logic_phase177.py` to test the refined intent execution and field extraction logic.
- **No Manual Tests**: Manual testing is strictly forbidden.

## Implementation Steps

### Step 1: Research & Reproduction (Internal)
- Analyze why the current Lead CRUD is "not working" (e.g., missing commits, silent failures, or incorrect data mapping).

### Step 2: Backend Enhancement
- Modify `AiAgentService` to correctly handle `CREATE`, `UPDATE`, and `DELETE` intents for Leads.
- Improve the regex-based field extraction for natural language updates.

### Step 3: Frontend Refinement
- Update `ai_agent.js` to ensure robust form wiring and graceful handling of successful redirects.

### Step 4: Verification
- Run the newly created unit tests to ensure all logic is correct and stable.

## Expected Outcome
- Users can create, update, and delete Leads directly via the AI Agent.
- All actions are correctly persisted to the database.
- The AI Agent provides clear and immediate feedback for each action.
- The AI Agent's table search remains client-side (no SQL execution for search) as per the previous rollback.
