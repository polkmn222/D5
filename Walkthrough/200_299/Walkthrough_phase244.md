## Phase 244 Walkthrough

- What changed:
  - Lead chat-form submit success now keeps the latest lead result visible in the newest chat area.
  - The workspace can still open/update for compatibility, but lead submit success no longer scrolls focus back to it.
  - Prompt/button-triggered actions now scroll the newly added user chat message into view.

- How it works:
  - `development/ai_agent/ui/frontend/static/js/ai_agent.js` now supports a non-focus-stealing workspace open mode.
  - The lead `OPEN_RECORD` branch inside `submitAgentChatForm(...)` uses that mode and scrolls the appended chat result instead.
  - `sendAiMessageWithDisplay(...)` now scrolls the newly appended user action message so the latest active area stays in view.

- How to verify:
  - Run:
    - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
  - Confirm the suite passes and that the lead submit success path preserves chat focus while keeping workspace compatibility.

- Limitation:
  - This phase improves visible continuity and attention flow first. It does not remove the underlying workspace fetch cost, so a second lead-only latency phase may still be the next safe step if more speed improvement is needed.
