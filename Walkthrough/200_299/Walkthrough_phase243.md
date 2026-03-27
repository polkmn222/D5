## Phase 243 Walkthrough

- What changed:
  - The shared chat-native form response now uses mode-specific wording for approved objects.
  - Create responses now say the form was opened in chat and tell the user to fill fields, then save.
  - Edit responses now say the form was opened in chat for the current record and tell the user to update fields, then save changes.
  - The legacy lead edit-form helper was aligned to the same wording pattern.

- How it works:
  - `development/ai_agent/ui/backend/service.py` now builds approved-object form-opening text and form descriptions from shared helpers.
  - `development/ai_agent/ui/backend/crud/lead.py` keeps the lead-specific helper but aligns its edit copy with the shared approved-object pattern.

- How to verify:
  - Run:
    - `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend/test_phase227_chat_native_open_form.py -q`
  - Confirm the suite passes and that approved-object create/edit `OPEN_FORM` responses use consistent text/description wording.

- Limitation:
  - This phase only normalizes `OPEN_FORM` wording and transition copy. It does not change fields, validation behavior, or the underlying UI model.
