# Phase 121 Walkthrough

## Result

- Template create/edit now shows byte counters, disables subject entry for SMS, and keeps MMS image upload/change available in the modal.
- MMS upload help now explains the allowed image rules and shows loading/error details when an upload fails.
- Send Message `AI Recommend` can now ask users which recommendation mode they want before applying the filter.

## Validation

- `PYTHONPATH=.gemini/development pytest -o cache_dir=.gemini/development/.pytest_cache .gemini/development/test/unit/messaging/ui/test_send_message_assets.py`
- Result: `4 passed`
