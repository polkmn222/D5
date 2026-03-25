# Manual Testing Strategy

## Goal

Manual testing covers high-value user flows and UI behaviors that automated tests do not fully validate, especially multi-step screen interactions, navigation, visual checks, and provider-adjacent workflows.

## Scope

Manual testing should focus on:

- dashboard access and navigation
- object list pages and detail pages
- object CRUD flows for core CRM entities
- lookup search and inline edit behavior
- bulk actions, sorting, tabs, and key buttons
- send-message and AI-agent flows when those areas are under review
- split-template ownership for messaging pages under `web/message/frontend/templates/`
- read-only detail exceptions such as the current message-send detail page

## Folder Roles

- `test/manual/smoke/`: fast checks run before releases or major demos
- `test/manual/regression/`: deeper manual scenarios across CRM objects and shared UI
- `test/manual/data_setup/`: reusable helpers for seeding or preparing test data
- `test/manual/ai_agent/`: active AI-agent-focused manual scripts
- `test/manual/legacy/`: historical scripts that should not be treated as canonical workflows
- `test/manual/evidence/`: phase-scoped manual evidence such as screenshots, logs, HTTP inspection notes, or exported reports

## Evidence Storage Rules

- Store each manual validation run under a phase-specific folder such as `test/manual/evidence/phase137/`.
- Keep the main run summary as a markdown file in that phase folder.
- Store server logs under a nested `logs/` folder inside the same phase folder when they help explain the run.
- Use descriptive filenames that include the port, route family, or execution context when helpful.
- If a helper script generates a report automatically, keep that generated report in the same phase evidence folder when practical.

## Environment Rules

- Use a dedicated PostgreSQL test database via `TEST_DATABASE_URL`.
- Use `D4_RESET_MANUAL_TEST_DB=1` only when a clean schema is explicitly needed.
- Start the app with `./run_crm.sh` unless a scenario requires a different launch mode.
- Treat provider-backed actions as environment-sensitive and verify the required credentials before running them.

## Execution Principles

- Run smoke checks before broader regression checks.
- Prefer seeded or prepared data over ad hoc production-like records.
- Record failures with reproducible steps, expected behavior, and the exact object or route involved.
- Move outdated scripts into `manual/legacy/` instead of treating them as current process.
- When validating messaging detail pages, confirm whether the page is intentionally read-only before treating missing inline-edit affordances as a bug.
