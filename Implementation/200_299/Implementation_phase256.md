## Phase 256 Implementation

### Scope
- Product-only non-submit `OPEN_RECORD` and selection-open chat-native expansion
- First safe entry point in the `product -> asset` roadmap

### Changes
- Updated [`service.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/backend/service.py) so `Manage product <id>` now returns an `OPEN_RECORD` response with a product chat card instead of falling back to generic selected-record text.
- Updated [`ai_agent.js`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/frontend/static/js/ai_agent.js) so product joins the chat-first preserved-focus set for non-submit `OPEN_RECORD`.
- Updated product selection/table `Open` to route through chat first using the existing `Manage product <id>` path.
- Updated [`ai-agent-crud-contract.md`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/docs/ai-agent-crud-contract.md) to record the new product continuity scope.

### Tests
- Updated source-level unit coverage in [`test_phase227_chat_native_open_form.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py).
- Updated DOM-level AI-agent continuity coverage in [`test_ai_agent_continuity_dom.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py).
- Verified with:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
