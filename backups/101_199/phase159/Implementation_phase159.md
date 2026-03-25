# Implementation Plan - Phase 159: AI Agent Feature Enhancement and CRUD Verification

## Goal
Enhance the AI Agent's user experience by showing the lead detail view after save/edit, fixing bulk selection actions ("Open", "Edit"), adding direct action buttons to agent tables, and verifying system-wide CRUD stability.

## User Review Required
> [!IMPORTANT]
> - **Selection Ready Actions**: "Open" and "Edit" for multiple selections will now be enabled. "Open" will open the first selected record in the workspace. "Edit" will open the first one in the edit form.
> - **Lead Detail Buttons**: "Edit" and "Delete" buttons will be added to the AI Agent's results table header (Selection Bar) and the Workspace header.

## Proposed Changes

### AI Agent Frontend
#### [MODIFY] [ai_agent.js](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/frontend/static/js/ai_agent.js)
- **updateSelectionBar**: Show "Open" and "Edit" in the summary text even for multiple selections. Enable "Open" and "Edit" buttons for `count >= 1`.
- **triggerSelectionOpen**: Update to allow opening the first selected record if multiple are selected.
- **triggerSelectionEdit**: Update to allow editing the first selected record if multiple are selected.
- **wireAgentInlineForm**: After a successful redirect (save/edit complete), call `openAgentWorkspace` for the record detail view instead of just fetching a chat card. This fulfills the "show open screen" requirement.
- **renderAgentResultsMarkup**: Add "Edit" and "Delete" buttons to the `table-controls` div above the table. These will trigger `triggerSelectionEdit()` and `triggerSelectionDelete()`.

#### [MODIFY] [ai_agent_panel.html](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/frontend/templates/ai_agent_panel.html)
- **Selection Bar**: Ensure the "Open" and "Edit" buttons are present and correctly mapped to JS functions.
- **Workspace Header**: Add "Edit" and "Delete" buttons to the right of the title in the workspace header (if not already present).

### CRUD Verification
#### [VERIFY] [test_core_crud.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/test/unit/crm/test_core_crud.py)
- Run all existing CRUD tests to ensure stability.
- Add a specific test case for Lead CRUD if any edge cases are found.

## Verification Plan

### Automated Tests
- **Unit Tests**:
    - Run `pytest .gemini/development/test/unit/crm/test_core_crud.py` to verify backend services.
    - Create a new test `test_ai_agent_flow_logic.py` to verify the logic of `AiAgentService` in returning appropriate intents after save.
- **Frontend Verification**:
    - Use the browser tool to verify:
        1. Create a lead via AI agent -> Save -> Verify Workspace opens with lead detail.
        2. Edit a lead via AI agent -> Save -> Verify Workspace refreshes with updated detail.
        3. Select 2 leads -> Verify "Selection Ready" bar shows Open/Edit as enabled.
        4. Click "Edit" in Selection Bar -> Verify first lead edit form opens.
        5. Verify "Edit" and "Delete" buttons exist above the agent result table.

### Manual Verification
- None (Prohibited by system prompt). All checks must be automated.
