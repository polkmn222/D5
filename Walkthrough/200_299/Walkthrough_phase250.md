## Phase 250 Walkthrough

### What Changed
- Opportunity non-submit `OPEN_RECORD` responses now stay chat-first in the active conversation area.
- The latest opportunity result/card is appended and scrolled into view before the compatibility workspace open runs.
- Workspace compatibility remains available, but it no longer steals visible focus for the scoped opportunity path.

### Verification
- Ran unit and DOM-level UI tests only.
- Manual testing was not performed.
- Command:
  - `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Result:
  - `47 passed`

### Scope Guardrails
- No backend contract changes
- No opportunity field or lookup redesign
- No multi-object continuity rewrite
- No submit-path behavior changes
