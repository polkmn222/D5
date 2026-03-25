# Phase 90 Implementation

## Changes

- Added `.gemini/development/web/backend/app/services/public_image_storage_service.py` to support Cloudinary-backed public image uploads with local filesystem fallback.
- Updated `.gemini/development/web/message/backend/router.py` so MMS template uploads now persist public URLs and provider keys through the shared storage service.
- Updated `.gemini/development/web/message/backend/routers/message_template_router.py` so legacy template image uploads use the same storage service and attachment metadata flow.
- Updated `.gemini/development/test/unit/messaging/router/test_upload_validation.py` with public-storage upload and cleanup coverage.
- Updated `.gemini/development/docs/deployment.md` and `.gemini/development/docs/SESSION_HANDOFF.md` to document Cloudinary configuration and the local-upload fallback behavior.

## Activation

- Cloudinary support turns on automatically when `CLOUDINARY_CLOUD_NAME` is present and either:
  - `CLOUDINARY_API_KEY` plus `CLOUDINARY_API_SECRET`, or
  - `CLOUDINARY_UNSIGNED_UPLOAD_PRESET`
- Without those values, uploads continue to use the local `/static/uploads/...` path.
