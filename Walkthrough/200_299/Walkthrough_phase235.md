# Phase 235 Walkthrough

## What Was Done
- The chat-native opportunity create/edit form now includes a `contact` lookup field.
- Opportunity edit forms now preload the selected contact name when a contact ID is already present.
- Opportunity form submit continues to send the selected contact record ID through the existing AI-agent submit flow.

## How It Works
- Backend form schema marks `contact` as a `lookup` control with `lookup_object: Contact`.
- On edit, the AI-agent resolves the opportunity’s saved contact ID into a display label for the chat form.
- The existing generic chat-native lookup UI handles:
  - search
  - select
  - clear
  - hidden-ID submit

## How To Verify
- Run:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
- Confirm the test file covers:
  - opportunity create form includes the contact lookup field
  - opportunity edit form preloads contact display label
  - opportunity create submit passes the selected contact ID unchanged

## Known Limitations
- This phase only adds the `contact` lookup slice.
- It does not add `brand`, `model`, `product`, or `asset`.
- It does not attempt full opportunity form parity.
- The next safest opportunity lookup slice after this phase would be `brand` and `model` only if you want to stay closer to core product context before adding `asset`.
