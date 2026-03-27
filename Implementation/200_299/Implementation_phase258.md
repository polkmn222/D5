Phase 258 Implementation

Summary
- Added brand-specific `MANAGE` / `OPEN_RECORD` handling backed by `VehicleSpecService.get_vehicle_spec`.
- Added a minimal brand chat card and extended the frontend open/view continuity path to brand.
- Reused the same bounded selection-open and preserved-focus pattern used for product and asset.

Files
- `development/ai_agent/ui/backend/service.py`
- `development/ai_agent/ui/frontend/static/js/ai_agent.js`
- `development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py`
- `development/test/unit/ai_agent/frontend/test_ai_agent_continuity_dom.py`
- `development/docs/ai-agent-crud-contract.md`
