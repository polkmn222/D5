# Task Phase 169: Responsive UI, Table Schema & Performance Optimization

## Objective
Optimize the AI Agent's responsiveness, data display, and interaction flow.

## Detailed Tasks

### 1. Attachment Exclusion & Backend Schema
- **File:** `.gemini/development/ai_agent/backend/service.py`
- [x] Exclude `attachment` from search/intent recognition.
- [x] Add `JOIN` to `Opportunity` query to include contact info.
- [x] Ensure `display_name` is computed correctly as `first_name + last_name`.

### 2. Frontend Schema & UI Logic
- **File:** `.gemini/development/ai_agent/frontend/static/js/ai_agent.js`
- [x] Update `AGENT_TABLE_SCHEMAS` with new user-provided columns.
- [x] Add `has_image` logic for `message_template` tables.
- [x] Refactor `toggleAiAgent` to prevent re-renders on size changes.
- [x] Add tooltips/labels for the new schema fields.

### 3. Responsive UI & CSS Refinement
- **File:** `.gemini/development/ai_agent/frontend/static/css/ai_agent.css`
- [x] Implement fluid layout for `#ai-agent-window`.
- [x] Set `min-width` and `overflow-x: auto` for `.results-container`.
- [x] Hide "Save & New" in form shell via CSS.

## Verification
- [x] Verify SQL generation for Opportunities via pytest.
- [ ] Verify Attachment exclusion via pytest.
- [ ] Verify no network/reload on minimize/maximize.
- [ ] Verify "Save & New" is hidden.

