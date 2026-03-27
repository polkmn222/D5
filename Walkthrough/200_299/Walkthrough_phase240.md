# Phase 240 Walkthrough

## What Was Done
- The chat-native opportunity create/edit form now includes an `asset` lookup field.
- Opportunity edit forms now preload the selected asset name when an asset ID is already present.
- Opportunity form submit continues to send the selected asset record ID through the existing AI-agent submit flow.

## How It Works
- Backend form schema marks `asset` as a `lookup` control with `lookup_object: Asset`.
- On edit, the AI-agent resolves the opportunity’s saved asset ID into a display label for the chat form.
- The existing generic chat-native lookup UI handles:
  - search
  - select
  - clear
  - hidden-ID submit

## How To Verify
- Run:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
- Confirm the test file covers:
  - opportunity create form includes the asset lookup field
  - opportunity edit form preloads asset display label
  - opportunity create submit passes the selected asset ID unchanged

## Known Limitations
- This phase only adds the `asset` lookup slice.
- It does not add amount/default syncing, automatic field updates, stronger relationship semantics, or broader opportunity asset behavior.
- If some saved opportunity asset IDs do not resolve cleanly, the preload display falls back safely to blank.
