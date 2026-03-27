Phase 257 Walkthrough

Behavior
- `Manage asset <id>` now returns `OPEN_RECORD` with an asset chat card.
- Asset selection/table `Open` now routes through chat first using `Manage asset <id>`.
- Asset non-submit `OPEN_RECORD` appends the latest result in chat and preserves chat focus before workspace open.
- Asset chat-card `Open Record` now uses explicit display-first chat routing.

Verification
- Ran:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Final result after the non-DB backend-test harness fix: passing within the later reruns that covered phases 257-259 together.

Notes
- Backend unit coverage now stubs `db.database` inside the unit test module so non-DB AI agent unit tests do not attempt live PostgreSQL inspection during collection.
