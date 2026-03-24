# Phase 119 Walkthrough

## Result

- SMS subjects are hidden in Send Message and template flows.
- Template/send content now supports merge fields such as `{Name}` and `{Model}`.
- SMS content over 90 bytes upgrades to LMS, and LMS/MMS content is capped at 2000 bytes.
- AI Agent lead rows no longer show the unused follow-up field.
- AI Agent selection is now action-first with `Open`, `Edit`, `Delete`, and `Send Message`, and delete confirmation uses clickable `[yes]` / `[cancel]` actions.

## Validation

- `PYTHONPATH=.gemini/development pytest -o cache_dir=.gemini/development/.pytest_cache .gemini/development/test/unit/ai_agent/backend/test_delete_confirmation.py .gemini/development/test/unit/ai_agent/frontend/test_assets.py .gemini/development/test/unit/ai_agent/backend/test_recommend_logic.py .gemini/development/test/unit/messaging/ui/test_send_message_assets.py .gemini/development/test/unit/messaging/test_messaging_detailed.py`
- Result: `33 passed`
- Runtime checks:
  - `http://127.0.0.1:8000/docs` -> `200`
  - `/messaging/ui` includes the hidden SMS subject preview state
