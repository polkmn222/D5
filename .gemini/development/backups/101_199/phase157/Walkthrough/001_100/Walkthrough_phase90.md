# Phase 90 Walkthrough

## Result

- The messaging runtime now supports public MMS image hosting through Cloudinary without breaking the current local upload path.
- Send Message uploads and legacy template image uploads both route through the same storage abstraction.
- Existing cleanup now removes stored assets through the shared storage service before the attachment record is soft-deleted.

## Validation

- `PYTHONPATH=.gemini/development pytest -o cache_dir=.gemini/development/.pytest_cache .gemini/development/test/unit/messaging/router/test_upload_validation.py`
- `PYTHONPATH=.gemini/development pytest -o cache_dir=.gemini/development/.pytest_cache .gemini/development/test/unit/messaging/providers/test_providers.py .gemini/development/test/unit/messaging/router/test_upload_validation.py .gemini/development/test/unit/messaging/test_messaging_detailed.py`
- `PYTHONPATH=.gemini/development pytest -o cache_dir=.gemini/development/.pytest_cache .gemini/development/test/unit/messaging/ui/test_send_message_assets.py .gemini/development/test/unit/messaging/router/test_template_subject.py`
- Result: `22 passed`

## Remaining Setup

- Cloudinary is not active until env values are supplied.
- Recommended production setup is signed Cloudinary credentials so uploads and deletes both work cleanly.
