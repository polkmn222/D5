# Implementation Plan - Phase 163: AI Agent Enhancements

This phase focuses on enhancing the AI Agent's CRUD flow, data table UI, and overall user experience based on the user's specific requirements.

## Proposed Changes

### AI Agent Frontend

#### [MODIFY] [ai_agent.js](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/frontend/static/js/ai_agent.js)
- **CRUD Feedback**:
    - Update `wireAgentInlineForm` to automatically trigger a "Show [object] [record_id]" chat command after a successful CREATE or UPDATE via the inline form.
    - Enhance `renderAgentChatCard` to include a header with `Edit` and `Delete` buttons for the record.
    - Implement `triggerSnapshotEdit` and `triggerSnapshotDelete`.
- **Data Table UI**:
    - Relocate the `.table-controls` bar to the top of the table.
    - Add a "Search in table..." text input to the control bar.
    - Implement `filterAgentTable(input)` for real-time client-side filtering.
    - Update the control bar buttons to: `[Select All] [Clear All] [Open] [Edit] [Delete]`.
    - Add instruction text "Select records to take action."
    - Move "Selected: ? items" count to below the buttons.
- **Selection & Interaction**:
    - Update `triggerSelectionOpen` and `triggerSelectionEdit` to use `appendChatMessage` for multi-selection warnings instead of `alert`.
    - Implement chat-based delete confirmation: `triggerSelectionDelete` will send a chat message with `[Yes]` and `[Cancel]` buttons.
    - Handle the `Yes` response to proceed with deletion and `Cancel` to abort.
    - Implement `removeAgentTableRow(objectType, recordId)` to immediately remove rows from all visible data tables upon deletion.
- **UX**:
    - Add auto-scroll logic in `appendChatMessage` and `appendAgentInlineFormMessage` to ensure the new content (table/form) is fully visible.

#### [MODIFY] [ai_agent.css](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/frontend/static/css/ai_agent.css)
- Add styles for the new table search input.
- Style the relocated control bar and its instruction text.
- Style the new snapshot card header and buttons.
- Ensure the selection count display matches the requirement.

#### [MODIFY] [ai_agent_panel.html](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/frontend/templates/ai_agent_panel.html)
- Ensure the structural compatibility for the relocated controls and hidden footer.
- Hide or remove the old `#ai-agent-selection-bar` as it will be integrated into the tables.

## Verification Plan

### Automated Tests
- **Backend CRUD**: Run `pytest .gemini/development/test/unit/test_ai_agent_comprehensive_crud.py` to ensure core AI Agent operations are still functional.
- **Table Filtering**: Create a new test `test_ai_agent_table_filter.py` (or similar) to verify the filtering logic if possible, or use a browser subagent for end-to-end verification.
- **Delete Integrity**: Run `pytest .gemini/development/test/unit/test_deletion_integrity.py`.

### Browser Verification
- **Table UI**: Verify the control bar is at the top with the search input and new buttons.
- **Search**: Verify typing in "Search in table..." filters the rows in real-time.
- **Selection**: Verify selecting records updates the "Selected: ? items" count.
- **Multi-select Warning**: Verify selecting 2+ records and clicking "Edit" shows the chat guidance.
- **Delete Flow**: Verify clicking "Delete" shows `[Yes]` `[Cancel]` in chat, and clicking `Yes` deletes the record and removes the row from the table.
- **Auto-scroll**: Verify the chat scrolls to the top of the table when it appears.
