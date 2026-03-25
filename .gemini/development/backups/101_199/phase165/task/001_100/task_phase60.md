# Phase 60 Task

## Scope
- Enforce MMS image restrictions for templates and message sends.
- Preserve and surface template images across Send Message and AI Agent flows.
- Improve duplicate-exclusion visibility in preview and summary.

## Acceptance Criteria
- MMS template uploads accept only JPG images up to 500KB.
- MMS sends require an uploaded attachment.
- Template image data is saved and reused in Send Message.
- AI Agent template queries expose image-related fields.
- Send summary shows skipped duplicate recipients.
- Unit tests pass.
