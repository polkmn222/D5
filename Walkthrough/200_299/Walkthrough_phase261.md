Phase 261 Walkthrough

Behavior
- AI-agent `SEND_MESSAGE` now appends a visible chat confirmation before the messaging workspace opens.
- The latest send confirmation is scrolled into view in chat.
- The messaging workspace still opens, but it now does so with preserved chat focus.
- Existing session handoff keys remain unchanged:
  - `aiAgentMessageSelection`
  - `aiAgentMessageTemplate`
- Template `Use In Send Message` now uses the same chat-first handoff continuity as the main `SEND_MESSAGE` path.

Verification
- Ran:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Result:
  - `97 passed in 2.29s`

Next Step
- Stop for a new planning pass on the later send-history / query / inspection side before implementing it.
