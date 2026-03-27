Phase 260 Walkthrough

Behavior
- `Manage message_template <id>` now returns `OPEN_RECORD` with a message-template chat card.
- Template selection/table `Open` now routes through chat first.
- Template non-submit `OPEN_RECORD` now appends the latest result in chat and preserves visible chat focus before workspace open.
- Template chat cards now support safe `Preview Image` when the stored path is already preview-safe for the current frontend behavior.
- Template chat cards now support `Use In Send Message` through the existing `startTemplateSendFromAgent(templateId)` handoff path.

Verification
- Ran:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Result:
  - `92 passed in 2.31s`

Notes
- This phase deliberately did not redesign the actual send flow.
- It also did not introduce new image upload, normalization, or storage behavior.
