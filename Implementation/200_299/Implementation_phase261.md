Phase 261 Implementation

Summary
- Added a shared frontend send-handoff continuity helper that:
  - preserves `aiAgentMessageSelection`
  - preserves `aiAgentMessageTemplate`
  - appends chat confirmation first
  - scrolls the latest chat confirmation into view
  - opens the messaging workspace with preserved chat focus
- Reused that helper for both the AI-agent `SEND_MESSAGE` intent branch and template `Use In Send Message`.

Files
- `development/ai_agent/ui/frontend/static/js/ai_agent.js`
- `development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py`
- `development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py`
- `development/docs/ai-agent-crud-contract.md`
