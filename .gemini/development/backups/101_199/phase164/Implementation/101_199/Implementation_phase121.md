# Phase 121 Implementation

## Changes

- Updated `.gemini/development/web/message/frontend/templates/send_message.html` so the template create/edit modal now shows live byte counters for subject and content.
- Locked SMS templates to subjectless mode in the modal by hiding and disabling subject input whenever the type is `SMS`.
- Improved MMS template editing in the modal with visible upload rules, upload loading text, and expandable error details when an image cannot be uploaded.
- Added a Send Message AI Recommend mode picker modal so users choose what kind of recommendations they want before filtering recipients.

## Result

- Template new/edit flows now make the SMS/LMS/MMS limits much clearer and support MMS image changes directly in the modal.
