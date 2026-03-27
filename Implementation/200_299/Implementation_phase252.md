## Phase 252 Implementation

### Scope
- Contact-only selection/table `Open` continuity
- Frontend-only
- Narrow scope

### Changes
- Updated [`ai_agent.js`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/frontend/static/js/ai_agent.js) so contact selection-driven `Open` now routes through `sendAiMessageWithDisplay(...)` using `Manage contact <id>`.
- Reused the existing contact chat-native `OPEN_RECORD` continuity path instead of opening the workspace directly from the selection trigger.
- Left lead and opportunity selection `Open` behavior intact.
- Updated the active markdown guidance in [`testing.md`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/docs/testing.md) and [`ai-agent-crud-contract.md`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/docs/ai-agent-crud-contract.md) so the current object-by-object continuity and testing strategy is documented in the same phase.

### Tests
- Updated source-level unit coverage in [`test_phase227_chat_native_open_form.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py).
- Updated DOM-level AI-agent continuity coverage in [`test_ai_agent_continuity_dom.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py).
- Verified with:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
