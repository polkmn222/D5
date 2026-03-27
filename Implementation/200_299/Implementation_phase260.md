Phase 260 Implementation

Summary
- Added message-template-specific `MANAGE` / `OPEN_RECORD` handling that returns a chat card instead of the legacy selected-record HTML block.
- Added a template chat card with image-aware actions: `Open Record`, `Preview Image` when a safe `/static/` path exists, and `Use In Send Message`.
- Extended the frontend chat-native open/view continuity path to `message_template` for selection `Open`, non-submit `OPEN_RECORD`, and card `Open Record`.

Files
- `development/ai_agent/ui/backend/service.py`
- `development/ai_agent/ui/frontend/static/js/ai_agent.js`
- `development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py`
- `development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py`
- `development/docs/ai-agent-crud-contract.md`
