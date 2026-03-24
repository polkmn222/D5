# Phase 141 Task

## Context

- Lookup creation paths are working, but users still report failures when editing or clearing lookup-backed values during real UI flows.
- The current detail pages mix two edit models: top-level `Edit` buttons open modals while field pencils switch to shared inline batch editing.
- The Send list view lost its row-level `Edit` and `Delete` controls, and message-send CRUD routes are incomplete for modal edit/delete behavior.

## Goals

- Align editable detail-page `Edit` buttons with the shared inline batch-edit behavior so they no longer diverge from the pencil affordance.
- Restore Send list row actions with working `Edit` and `Delete` behavior backed by message create/update/delete routes.
- Verify lookup edit and clear flows across the shared detail/edit surfaces and add focused tests for the updated behavior.
