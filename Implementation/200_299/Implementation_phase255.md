## Phase 255 Implementation

### Scope
- Approved-object-wide delete-confirmation continuity and scroll polish
- Frontend-only
- Narrow scope

### Changes
- Updated [`ai_agent.js`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/frontend/static/js/ai_agent.js) so card-triggered `Delete` confirmations now append in chat and scroll the latest confirmation into view.
- Updated selection/table `Delete` confirmations to do the same.
- Included the existing delete-cancel path in the same continuity treatment by scrolling the latest user/cancelled messages when that shortcut path is used.
- Left actual delete resolution semantics, pending-delete state handling, and backend behavior unchanged.

### Tests
- Updated source-level unit coverage in [`test_phase227_chat_native_open_form.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py).
- Updated DOM-level AI-agent continuity coverage in [`test_ai_agent_continuity_dom.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py).
- Verified with:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
