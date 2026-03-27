Phase 259 Walkthrough

Behavior
- `Manage model <id>` now returns `OPEN_RECORD` with a model chat card.
- Model selection/table `Open` now routes through chat first.
- Model non-submit `OPEN_RECORD` now appends the latest result in chat and preserves chat focus before workspace open.
- Model chat-card `Open Record` now uses explicit display-first routing.

Verification
- Ran:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Result after the model additions: `84 passed in 1.98s`

Decision Point
- Reached the `send/template` group after this phase.
- Template flows already combine preview UI, image paths, and send handoff, so that group needs a brief design decision before implementation continues.
