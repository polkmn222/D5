## Phase 251 Implementation

### Scope
- Opportunity-only selection/table `Open` continuity
- Frontend-only
- Narrow scope

### Changes
- Updated [`ai_agent.js`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/frontend/static/js/ai_agent.js) so opportunity selection-driven `Open` now routes through `sendAiMessageWithDisplay(...)` using `Manage opportunity <id>`.
- Kept the existing downstream opportunity `OPEN_RECORD` continuity path unchanged, so the newest chat result still appears first and workspace compatibility remains downstream.
- Left lead selection `Open` behavior unchanged.
- Left contact selection `Open` unchanged in this phase.

### Tests
- Updated source-level unit coverage in [`test_phase227_chat_native_open_form.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py).
- Updated DOM-level AI-agent continuity coverage in [`test_ai_agent_continuity_dom.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py).
- Verified with:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
