Phase 257 Implementation

Summary
- Added asset-specific `MANAGE` / `OPEN_RECORD` handling in the AI agent backend.
- Added a minimal asset chat card with `Open Record`, `Edit`, and `Delete`.
- Extended the frontend chat-native open/view continuity path to asset for selection `Open`, non-submit `OPEN_RECORD`, and card `Open Record`.

Files
- `development/ai_agent/ui/backend/service.py`
- `development/ai_agent/ui/frontend/static/js/ai_agent.js`
- `development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py`
- `development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py`
- `development/docs/ai-agent-crud-contract.md`
