# AI Agent Lead CRUD Enhancement & Natural Transition (Phase 171)

This plan aims to fix issues with Lead CRUD operations in the AI Agent and implement a Salesforce-style natural transition to the record view upon successful creation or modification. This is designated as **Phase 171** as Phase 170 already exists in the documentation folders.

## Proposed Changes

### AI Agent Backend

#### [MODIFY] [service.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/backend/service.py)
- Refine `CREATE` intent handling for Leads: Ensure `LeadService.create_lead` is called correctly and the response triggers a transition.
- Refine `UPDATE` intent handling for Leads: Ensure `LeadService.update_lead` is called correctly.
- Refine `DELETE` intent handling: Ensure `_delete_record` correctly calls `LeadService.delete_lead`.
- Update `_execute_intent` to include a new `action: "OPEN_RECORD"` or similar signal in the response when a lead is created or updated, instructing the frontend to open the record workspace.

### AI Agent Frontend

#### [MODIFY] [ai_agent.js](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/frontend/static/js/ai_agent.js)
- Update `sendAiMessage` to handle the new `OPEN_RECORD` action from the backend.
- Implement logic to automatically call `openAgentWorkspace` with the correct URL when a lead is successfully created or updated.
- Ensure success/failure notifications are displayed clearly in the chat bubble.

## Verification Plan

### Automated Tests
- Run existing unit tests:
  - `pytest .gemini/development/test/unit/ai_agent/backend/test_lead_natural_transition.py`
  - `pytest .gemini/development/test/unit/ai_agent/backend/test_lead_flow_consistency.py`
- Create a new test `test_lead_crud_logic_phase171.py` to specifically verify:
  - Correct calling of `LeadService` methods.
  - Presence of the transition signal in the backend response.
  - Proper handling of error cases (e.g., missing fields, database errors).

### Manual Verification
- **None** (As per user instructions: "manual test is strictly prohibited"). All verification will be done via unit tests.
