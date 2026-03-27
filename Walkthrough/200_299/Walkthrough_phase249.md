## Phase 249 Walkthrough

### What Changed

Contact-only non-submit `OPEN_RECORD` flows now preserve chat continuity more like lead:

- contact prompt-driven open/manage flows:
  - append the newest contact result/card in chat first
  - scroll the latest chat result into view
  - open the workspace without stealing visible focus
- contact card `Open Record` actions:
  - keep the same round-trip through chat
  - now preserve chat continuity when the contact `OPEN_RECORD` response arrives
- contact prompt/button-triggered actions:
  - keep the newest active chat area in view in the DOM-level continuity harness

### Why It Feels More Continuous

- The newest contact result remains visible in the conversation instead of the workspace immediately taking attention.
- Workspace compatibility is preserved.
- Contact now feels closer to lead in day-to-day chat usage without broadening into a larger rewrite.

### Validation

- Ran:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Result:
  - `44 passed`

### Not Changed

- Lead non-submit `OPEN_RECORD` behavior from phase 248.
- Opportunity non-submit `OPEN_RECORD` behavior.
- Submit-path no-auto-open behavior from phases 245-247.
- Backend contracts.
- Browser automation setup.
