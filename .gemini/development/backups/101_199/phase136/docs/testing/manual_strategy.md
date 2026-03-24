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

## Folder Roles

- `test/manual/smoke/`: fast checks run before releases or major demos
- `test/manual/regression/`: deeper manual scenarios across CRM objects and shared UI
- `test/manual/data_setup/`: reusable helpers for seeding or preparing test data
- `test/manual/ai_agent/`: active AI-agent-focused manual scripts
- `test/manual/legacy/`: historical scripts that should not be treated as canonical workflows
- `test/manual/evidence/`: local screenshots, logs, or exported notes; keep this out of git

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
