# Phase 238 Walkthrough

## What Was Done
- The chat-native opportunity create/edit form now includes a `product` lookup field.
- Opportunity edit forms now preload the selected product name when a product ID is already present.
- Opportunity form submit continues to send the selected product record ID through the existing AI-agent submit flow.

## How It Works
- Backend form schema marks `product` as a `lookup` control with `lookup_object: Product`.
- On edit, the AI-agent resolves the opportunity’s saved product ID into a display label for the chat form.
- The existing generic chat-native lookup UI handles:
  - search
  - select
  - clear
  - hidden-ID submit

## How To Verify
- Run:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
- Confirm the test file covers:
  - opportunity create form includes the product lookup field
  - opportunity edit form preloads product display label
  - opportunity create submit passes the selected product ID unchanged
  - `asset` remains absent

## Known Limitations
- This phase only adds the `product` lookup slice.
- It does not add `asset`.
- It does not attempt brand/model/product dependent behavior or broader opportunity form parity.
- If some saved opportunity product IDs do not resolve cleanly, the preload display falls back safely to blank.
