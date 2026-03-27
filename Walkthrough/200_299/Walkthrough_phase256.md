## Phase 256 Walkthrough

### What Changed
- Product now joins the chat-native open/view path for non-submit `OPEN_RECORD`.
- Product selection/table `Open` now appends the user/action message in chat first and routes through `Manage product <id>`.
- The resulting product open response now stays anchored in the latest chat area before the workspace opens with preserved chat focus.
- Asset was intentionally left out of this phase.

### Verification
- Ran unit and DOM-level UI tests only.
- Manual testing was not performed.
- Command:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Result:
  - `63 passed`

### Scope Guardrails
- No product create/edit chat-form parity
- No asset expansion in this phase
- No Send Message work
- No broader grouped-object rollout beyond product
