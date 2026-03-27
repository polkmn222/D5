## Phase 254 Implementation

### Scope
- Opportunity-only chat-card `Send Message` parity
- Narrow object-specific phase

### Changes
- Updated [`service.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/ai_agent/ui/backend/service.py) so opportunity chat cards now include the `Send Message` action alongside `Open Record`, `Edit`, and `Delete`.
- Updated the opportunity chat-card hint copy so it mentions sending a message.
- Reused the existing frontend card-action handler and existing chat-native messaging path without redesigning the messaging flow.
- Updated the opportunity card-action expectation in [`ai-agent-crud-contract.md`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/docs/ai-agent-crud-contract.md).

### Tests
- Updated source-level unit coverage in [`test_phase227_chat_native_open_form.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py).
- Updated DOM-level AI-agent continuity coverage in [`test_ai_agent_continuity_dom.py`](/Users/sangyeol.park@gruve.ai/Documents/D5/development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py).
- Verified with:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
