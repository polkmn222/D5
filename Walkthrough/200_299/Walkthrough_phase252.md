## Phase 252 Walkthrough

### What Changed
- Contact selection/table `Open` no longer jumps directly to the workspace from the initial trigger.
- The selection-open action now appends the visible user/action message in chat first and sends `Manage contact <id>`.
- That request then continues through the existing contact `OPEN_RECORD` chat-first continuity path.
- The docs now reflect the active object-by-object delivery strategy and the current frontend testing rules for UI phases.

### Verification
- Ran unit and DOM-level UI tests only.
- Manual testing was not performed.
- Command:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Result:
  - `52 passed`

### Scope Guardrails
- No backend contract changes
- No contact `Send Message` parity changes
- No contact edit-form model changes
- No multi-object selection cleanup
