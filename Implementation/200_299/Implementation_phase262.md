Phase 262 Implementation

Summary
- Added deterministic send-history query resolution for generic `messages` requests.
- Routed `show messages` and `show recent messages` directly to the existing `message_send` list SQL surface.
- Documented the initial `message_send` history rollout as generic query/list only.

Files
- `development/ai_agent/ui/backend/service.py`
- `development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py`
- `development/docs/ai-agent-crud-contract.md`
