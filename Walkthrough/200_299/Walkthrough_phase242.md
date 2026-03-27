# Phase 242 Walkthrough

## What Was Done
- The lead-specific card still uses the lead-specific model, but its action ordering and hint text now align more closely with the shared approved-object behavior pattern.
- Contact and opportunity behavior from Phase 241 was left unchanged.

## How It Works
- Lead card actions now prioritize the shared pattern:
  - open
  - edit
  - delete
  - then the lead-specific `send_message` action
- Lead hint text now explicitly mentions:
  - editing in chat
  - opening the full record
  - sending a message

## How To Verify
- Run:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
- Confirm the test file covers:
  - lead `OPEN_RECORD` still uses `lead_paste`
  - lead subtitle remains stable
  - lead action order is now `open`, `edit`, `delete`, `send_message`
  - lead hint mentions editing and opening the full record

## Known Limitations
- Lead still uses a lead-specific card type rather than the generic `record_paste` type, by design.
- This phase does not attempt to collapse lead into the generic card model.
- If a remaining lead-specific nuance still feels different, that is intentional where it preserves useful lead-specific behavior.
