# Walkthrough - Phase 60

## What Changed
This phase tightened MMS safety rules and made template images first-class in the messaging workflow.

## MMS Safety
- MMS templates now require JPG images under 500KB.
- The same rule is enforced in the browser and on the backend upload endpoint.
- Sending an MMS without an attachment is blocked.

## Template Images
- Template images can now be uploaded from the Send Message template modal.
- Those images are saved in a reusable form and can be applied back to the compose area.
- AI Agent message-template queries now expose image-related fields so templates are easier to inspect there too.

## Delivery Transparency
- Preview now shows duplicate-exclusion effects more clearly.
- Final send summary shows which recipients were skipped because of duplicate phone numbers.
