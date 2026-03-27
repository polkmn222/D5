Phase 259 Implementation

Summary
- Added model-specific `MANAGE` / `OPEN_RECORD` handling backed by `ModelService.get_model`.
- Added a minimal model chat card with brand lookup display.
- Extended the frontend chat-native open/view continuity path to model for selection `Open`, non-submit `OPEN_RECORD`, and card `Open Record`.

Files
- `development/ai_agent/ui/backend/service.py`
- `development/ai_agent/ui/frontend/static/js/ai_agent.js`
- `development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py`
- `development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py`
- `development/docs/ai-agent-crud-contract.md`
