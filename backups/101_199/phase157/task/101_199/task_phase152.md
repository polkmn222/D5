# Phase 152 Task

## Context

- The user reported that lead detail pencil edits were not working as expected.
- The user also reported that list-view `Edit` flows were not usable, asset related data was not auto-reflecting after edits, and all non-message objects should support message-style modal editing from the detail header while still keeping pencil inline editing.
- The backups workflow was re-read from `.gemini/development/backups/README.md`, and the active docs were re-reviewed before implementation.

## Goals

- Make non-message detail headers open modal edit forms while preserving pencil-based inline editing.
- Fix lead inline edit save behavior for the computed `Name` field.
- Fix asset modal edit save behavior from list/detail flows and ensure asset related cards reflect current linked lookups.
- Keep opportunity related tabs free of the linked lead card.
- Re-run required unit tests and focused manual verification.

## Success Criteria

- `Edit` on core detail pages opens the shared modal form like message-send detail.
- Pencil editing still works on supported editable fields.
- Lead inline save no longer silently fails for `Name` updates.
- Asset modal edits persist correctly and asset related tabs reflect updated Brand / Model / Product links.
- Full unit suite passes and focused manual verification is recorded.
