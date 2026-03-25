# Phase 60 - MMS Image Guardrails and Template Image Visibility

## Goals
- Enforce JPG-only, 500KB max uploads for MMS templates.
- Enforce the same guardrails on the Send Message screen.
- Make template images visible and reusable in Send Message and AI Agent flows.
- Improve preview/send trust with duplicate exclusion visibility.

## Implemented Changes

### 1. MMS Upload Guardrails
- Added MMS image upload controls to the template modal on `send_message.html`.
- MMS template images now require:
  - `.jpg` or `.jpeg`
  - `image/jpeg` or `image/jpg`
  - file size `<= 500KB`
- The messaging upload endpoint now enforces the same validation server-side.

### 2. Template Image Persistence
- Uploaded template images now save to a static path and return `image_url`.
- Template save payload now includes:
  - `file_path`
  - `attachment_id`
  - `image_url`
- Backend template create/update paths now preserve `image_url`.

### 3. Send Message Enforcement
- `sendPreparedMessages()` now validates the current message config.
- MMS sends are blocked unless an attachment is present.

### 4. Preview / Summary Improvements
- Duplicate review now shows excluded recipient counts more clearly.
- Final send summary now includes skipped duplicate recipients as `Excluded Duplicate Phone`.

### 5. AI Agent Template Visibility
- AI Agent message-template query defaults now include:
  - `content`
  - `image_url`
  - `attachment_id`
  - `file_path`
- AI Agent manage text now indicates when a template has an image.

## Files Changed
- `.gemini/development/frontend/templates/send_message.html`
- `.gemini/development/backend/app/api/messaging_router.py`
- `.gemini/development/ai_agent/backend/service.py`

## Backup
- `.gemini/development/backups/phase60/`
