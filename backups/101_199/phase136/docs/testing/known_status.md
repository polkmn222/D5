# Known Test Status

## Current Full Unit Reference

- Command: `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit -rs -q`
- Last reviewed status: `9 failed, 324 passed, 4 skipped`

## Known Failing Tests

### Likely runtime or contract issues

- `test/unit/ai_agent/backend/test_conversation_context.py::test_recent_reference_does_not_leak_between_conversations`
  - Current behavior resolves `show the lead I just created` as a `QUERY` even in a different conversation.
  - Treat this as a likely AI flow or pre-classifier contract issue until resolved.
- `test/unit/messaging/router/test_upload_validation.py::test_legacy_template_upload_uses_public_storage_service`
  - Current failure indicates direct-call signature mismatch for `template_upload(...)`.
- `test/unit/messaging/router/test_upload_validation.py::test_legacy_clear_image_removes_stored_attachment`
  - Current failure indicates direct-call signature mismatch or outdated invocation shape for `clear_template_image(...)`.
- `test/unit/messaging/templates/test_list_view.py::test_list_templates_includes_content`
  - Current failure is affected by request/query-param assumptions and should be reviewed before changing runtime behavior.

### Likely outdated test expectations

- `test/unit/ai_agent/backend/test_messaging_crud.py::test_ai_message_template_crud_flow`
  - Delete success text now uses `Message Template` rather than the shorter `Template` label.
- `test/unit/ai_agent/backend/test_selection_context.py::test_selection_payload_is_saved_in_conversation_context`
  - Conversation selection state now normalizes `labels` as part of the stored payload shape.
- `test/unit/messaging/router/test_template_subject.py::test_create_template_passes_subject_to_service`
  - Current messaging rules intentionally clear SMS subjects.
- `test/unit/ui/shared/test_inline_edit_unity.py::test_pencil_icon_existence[messages/detail_view.html]`
  - The current message detail page is intentionally read-only.
- `test/unit/ui/shared/test_inline_edit_unity.py::test_pencil_icon_structure[messages/detail_view.html]`
  - The current message detail page is intentionally read-only.

## Known Skipped Tests

- `test/unit/ui/shared/test_batch_edit_ui.py` currently skips four message/message-template cases because it looks for:
  - `.gemini/development/web/frontend/templates/messages/detail_view.html`
  - `.gemini/development/web/frontend/templates/message_templates/detail_view.html`
- The active files live under:
  - `.gemini/development/web/message/frontend/templates/messages/detail_view.html`
  - `.gemini/development/web/message/frontend/templates/message_templates/detail_view.html`

## Usage Rule

- Use this file to document known test mismatches while docs, tests, and runtime behavior are being brought back into alignment.
- Do not treat entries here as permanent waivers; remove or update them when the runtime or tests are corrected.
