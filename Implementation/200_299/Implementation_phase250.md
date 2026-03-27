## Phase 250 Implementation

### Scope
- Opportunity-only non-submit `OPEN_RECORD` continuity/scroll polish
- Frontend-only
- Narrow scope

### Changes
- Updated the AI agent non-submit `OPEN_RECORD` handling in `development/ai_agent/ui/frontend/static/js/ai_agent.js` so `opportunity` now uses the same preserved-chat-focus path already used for `lead` and `contact`.
- Kept the opportunity result/card appended in the latest chat area before the workspace open call.
- Preserved workspace compatibility while preventing the workspace from stealing visible focus in the opportunity non-submit `OPEN_RECORD` path.
- Left lead, contact, and submit-path behavior unchanged.

### Tests
- Updated source-level unit coverage in `development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py`.
- Updated DOM-level AI-agent continuity coverage in `development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py`.
- Verified with:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
