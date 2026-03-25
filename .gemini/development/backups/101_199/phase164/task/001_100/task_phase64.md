# Phase 64 Task

## Scope
- Refine the in-chat selection guidance.
- Add template image preview/lightbox support.
- Make template-aware send-message requests explicit and safe.

## Acceptance Criteria
- Selection guidance explains that CRUD can continue before messaging.
- AI Agent template thumbnails are clickable.
- Send Message template preview image is clickable.
- Template-based send requests without current template ask for template context first.
- Regression tests pass.
