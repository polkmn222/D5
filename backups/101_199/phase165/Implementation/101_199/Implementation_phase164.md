# Implementation Plan - Phase 164: AI Agent CRUD and UI/UX Enhancements

This phase completes the AI Agent enhancements for CRUD flow, data table UI, and intelligent selection logic, ensuring a seamless user experience.

## Objective
1.  **CRUD Flow & Feedback**:
    -   Extend the snapshot card to support `Contact`, `Opportunity`, `Product`, `Asset`, `Brand`, `Model`, and `MessageTemplate`.
    -   Ensure successful `CREATE` and `UPDATE` operations via AI Agent (both direct and inline-form) return the appropriate snapshot card.
    -   Ensure `Edit` and `Delete` buttons are prominently placed in the snapshot card header.
    -   Verify immediate row removal from all visible tables upon record deletion.
2.  **Data Table UI**:
    -   Verify and refine the table control bar: `[Select All] [Clear All] [Open] [Edit] [Delete]` buttons in one row.
    -   Ensure "Select records to take action." instruction is at the top.
    -   Ensure "Selected: ? items" is displayed below the buttons.
    -   Hide the legacy selection bar (`#ai-agent-selection-bar`) structurally.
3.  **Intelligent Selection**:
    -   Provide localized chat guidance ("한 번에 하나의 레코드만 열거나 수정할 수 있습니다" / "Open/Edit works on one record at a time") when multiple records are selected for single-record actions.
    -   Ensure chat-based delete confirmation is used consistently for both snapshot cards and data tables.
4.  **UX**:
    -   Refine auto-scroll logic to scroll to the top of data tables and the start of inline forms.

## Proposed Changes

### AI Agent Backend

#### [MODIFY] `ai_agent/backend/service.py`
-   Rename `_build_lead_chat_card` to `_build_chat_card` and extend it to support all core CRM objects.
-   Update `_execute_intent` for `CREATE` and `UPDATE` to use `_build_chat_card` for all supported objects, not just leads.
-   Ensure `_resolve_delete_confirmation` returns localized text based on `language_preference`.

### AI Agent Frontend

#### [MODIFY] `ai_agent/frontend/static/js/ai_agent.js`
-   Update `getAiAgentUiCopy` to include localized strings for multi-selection constraints.
-   Update `triggerSelectionOpen` and `triggerSelectionEdit` to use localized messages from `getAiAgentUiCopy`.
-   Refine `appendChatMessage` scroll logic to ensure `.results-container` is scrolled to the top.
-   Refine `appendAgentInlineFormMessage` scroll logic to ensure the form start is visible.
-   Ensure `removeAgentTableRow` correctly handles all object types.

#### [MODIFY] `ai_agent/frontend/templates/ai_agent_panel.html`
-   Double-check that `#ai-agent-selection-bar` is hidden and doesn't interfere with the layout.

## Verification Plan

### Automated Tests (Unit)
-   **Backend Card Generation**: Add tests to `test_ai_agent_flow_logic.py` to verify `_build_chat_card` returns correct metadata for different object types.
-   **Backend Intent Execution**: Verify `CREATE` and `UPDATE` intents return the expected `chat_card` for non-lead objects.

### Manual Verification (Script-based or Observation)
-   Since manual browser testing is prohibited, I will verify the generated HTML markup in unit tests where possible.
-   Ensure all JS functions are syntactically correct and follow the logic described.
