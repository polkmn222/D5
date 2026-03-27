Phase 262 Walkthrough

Behavior
- `show messages` now resolves deterministically to the `message_send` query/list surface.
- `show recent messages` now resolves deterministically to the same `message_send` list surface.
- Results stay list-style in chat and use the existing `message_send` ordering by `sent_at DESC`.
- Existing send handoff continuity from Phase 261 remains unchanged.
- Existing template handoff behavior from Phase 260 remains unchanged.

Verification
- Ran:
  - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
- Result:
  - `62 passed in 0.31s`

Notes
- This phase intentionally does not add recipient/date/template filter semantics.
- It also does not add send detail/open continuity yet.
