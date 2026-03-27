# Phase 236 Walkthrough

## What Was Done
- The chat-native opportunity create/edit form now includes a `brand` lookup field.
- Opportunity edit forms now preload the selected brand name when a brand ID is already present.
- Opportunity form submit continues to send the selected brand record ID through the existing AI-agent submit flow.

## How It Works
- Backend form schema marks `brand` as a `lookup` control with `lookup_object: Brand`.
- On edit, the AI-agent resolves the opportunity’s saved brand ID into a display label for the chat form.
- The existing generic chat-native lookup UI handles:
  - search
  - select
  - clear
  - hidden-ID submit

## How To Verify
- Run:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
- Confirm the test file covers:
  - opportunity create form includes the brand lookup field
  - opportunity edit form preloads brand display label
  - opportunity create submit passes the selected brand ID unchanged

## Known Limitations
- This phase only adds the `brand` lookup slice.
- It does not add `model`, `product`, or `asset`.
- It does not attempt broader opportunity form parity.
- If this lands cleanly, `model` would still be the next safest opportunity lookup slice after `brand`.
