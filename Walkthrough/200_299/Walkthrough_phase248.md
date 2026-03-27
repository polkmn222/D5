## Phase 248 Walkthrough

### What Changed

Lead-only non-submit `OPEN_RECORD` flows now behave more like a continuous chat thread:

- prompt-driven lead open/manage flows:
  - append the newest lead result/card in chat first
  - scroll the latest chat result into view
  - open the workspace without letting it steal visible focus
- lead card `Open Record` actions:
  - keep the same round-trip through chat
  - now preserve chat continuity when the lead `OPEN_RECORD` response arrives
- lead selection/table `Open` actions:
  - still route through chat paste behavior
  - now keep the latest lead result visible in the chat area

### Why It Feels More Continuous

- The newest lead result stays visible in the active conversation area instead of the workspace immediately pulling visual attention away.
- The workspace still opens for compatibility, but it does so in preserve-chat-focus mode for lead non-submit `OPEN_RECORD`.
- Prompt/button-triggered lead actions keep the conversation feeling more downward and ChatGPT-like.

### Validation

- First run failed at collection because the active environment tried to resolve a remote PostgreSQL host during import.
- Re-ran the focused suite with a unit-test DB override:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Result:
  - `41 passed`

### Not Changed

- Submit-path no-auto-open behavior from phases 245-247.
- Contact non-submit `OPEN_RECORD` behavior.
- Opportunity non-submit `OPEN_RECORD` behavior.
- Backend contracts.
- Browser automation setup.
