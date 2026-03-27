# Phase 237 Walkthrough

## What Was Done
- The chat-native opportunity create/edit form now includes a `model` lookup field.
- Opportunity edit forms now preload the selected model name when a model ID is already present.
- Opportunity form submit continues to send the selected model record ID through the existing AI-agent submit flow.

## How It Works
- Backend form schema marks `model` as a `lookup` control with `lookup_object: Model`.
- On edit, the AI-agent resolves the opportunity’s saved model ID into a display label for the chat form.
- The existing generic chat-native lookup UI handles:
  - search
  - select
  - clear
  - hidden-ID submit

## How To Verify
- Run:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
- Confirm the test file covers:
  - opportunity create form includes the model lookup field
  - opportunity edit form preloads model display label
  - opportunity create submit passes the selected model ID unchanged
  - `product` and `asset` remain absent

## Known Limitations
- This phase only adds the `model` lookup slice.
- It does not add `product` or `asset`.
- It does not attempt brand/model dependent filtering or broader opportunity form parity.
- If some saved opportunity model IDs do not resolve cleanly, the preload display falls back safely to blank.
