# Implementation Phase 169: Responsive UI, Table Schema & Performance Optimization

## Goal
Optimize the AI Agent experience by:
1.  Implementing a **Responsive UI** (fluid window, sidebar, and auto-scrolling tables).
2.  Updating the **Table Schema** (Data columns) to align with Salesforce-style requirements.
3.  Excluding `attachment` objects from search.
4.  Fixing **UI Performance** to ensure no reloads occur during minimize/maximize actions.
5.  Refining **Lead Forms** by hiding the "Save & New" button and improving transitions.

## Proposed Changes

### 1. Attachment Exclusion & Backend Schema
#### [MODIFY] [service.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/backend/service.py)
*   **Object Exclusion**: Update `process_query` and `IntentPreClassifier` (if applicable) to ensure `attachment` is never picked up as a search target.
*   **Opportunity Join**: Update `_default_query_parts` for `opportunity` to `LEFT JOIN contacts` and select `contact_display_name` and `contact_phone`.
*   **Message Template**: Ensure `image_url` and `attachment_id` are returned for image presence checking.

### 2. Frontend Schema & UI Logic
#### [MODIFY] [ai_agent.js](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/frontend/static/js/ai_agent.js)
*   **Update `AGENT_TABLE_SCHEMAS`**: Set the new column sets for `lead`, `contact`, `opportunity`, `message_template`, etc.
*   **Display Name Logic**: Enforce `display_name = first_name + last_name` in `getAgentFieldValue`.
*   **Performance Fix**: Refactor `toggleAiAgent` and `syncAiAgentWindowState` to ensure the window state changes are purely CSS-driven and do not trigger any `fetch` or `innerHTML` resets.
*   **Message Template "Image" Column**: Update `getAgentFieldValue` to return "True/False" or an icon for the image presence.

### 3. Styling & Form Refinement
#### [MODIFY] [ai_agent.css](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/frontend/static/css/ai_agent.css)
*   **Responsive Window**: Use fluid units and media queries for `#ai-agent-window`.
*   **Hide "Save & New"**: Add `.agent-inline-form-shell button[data-submit-mode="save-new"] { display: none !important; }`.

## Verification Plan

### Automated Tests
*   **SQL Verification**: `pytest .gemini/development/test/unit/ai_agent/backend/test_opportunity_join.py` (New test for joined fields).
*   **Exclusion Verification**: `pytest .gemini/development/test/unit/ai_agent/backend/test_attachment_exclusion.py`.

### Manual Observation
*   Verify no "loading" state occurs on window resize/maximize.
*   Verify Opportunity table shows Contact details.
