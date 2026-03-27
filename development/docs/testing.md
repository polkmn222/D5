# Testing Policy

## Purpose

This document is the active testing policy for the D5 repository.

## Core Rules

- Unit tests are mandatory for any code change that affects logic, behavior, routing, parsing, data flow, or response contracts.
- Manual testing is forbidden.
- Do not treat manual browser checks, local click-throughs, or ad hoc API poking as acceptable verification.
- UI or frontend behavior changes must use unit tests plus narrow DOM-level UI tests for the changed UI behavior only.
- Non-UI phases should use unit tests only unless the user explicitly asks for a different test type.
- Browser automation is not part of the default workflow and must not be added unless the user explicitly approves it later.
- Documentation-only tasks do not require unit test execution unless the user explicitly asks for it.
- SQLite compatibility is not a project goal.
- PostgreSQL is the only supported database target for any DB-backed test.

## What Counts As A Required Unit-Test Change

Add or update unit tests when changing:

- service logic
- router behavior
- response normalization
- request parsing
- deterministic intent resolution
- conversation state handling
- CRUD behavior
- list-view behavior
- delete confirmation logic

## Minimum Standard For Future `development/ai_agent` CRUD Work

Future `development/ai_agent` CRUD changes must include unit coverage for:

1. deterministic object resolution
2. deterministic action resolution
3. supported-object create flow
4. supported-object update flow
5. supported-object query flow
6. safe fallback behavior for ambiguous requests
7. safe fallback behavior for unsupported requests
8. response contract preservation for the frontend

## Minimum Assertions For AI Agent CRUD Tests

For each supported object, tests should verify:

- `CREATE` returns an `OPEN_RECORD`-style response on success
- incomplete create requests use `OPEN_FORM` when the minimum deterministic required fields are missing
- the create response includes the created record identifier and open-record target
- `UPDATE` returns a refreshed `OPEN_RECORD`-style response on success
- `QUERY` for requests such as `all [object]` returns list-view-style results
- `MANAGE`, `OPEN_RECORD`, and `OPEN_FORM` stay consistent with the documented contract
- ambiguous requests do not hallucinate fields, IDs, SQL, or unsupported behavior

## Supported Object Set For CRUD Coverage

The future generalized `development/ai_agent` CRUD surface must cover:

- lead
- contact
- opportunity
- product
- asset
- brand
- model
- message_template

## Execution Guidance

- Prefer focused unit suites over broad unfocused runs.
- Use `PYTHONPATH=development`.
- Pure unit tests should prefer mocks and should avoid real DB dependence entirely.
- Keep DOM-level frontend tests minimal, AI-agent-specific, and behavior-specific when a UI phase changes continuity, scrolling, or visible focus behavior.
- Any test that exercises repository code, ORM behavior, persistence, schema constraints, or query behavior must be marked and run as an integration test.
- DB-backed tests must use `TEST_DATABASE_URL` and PostgreSQL only.
- Do not use `DATABASE_URL=sqlite:///:memory:` for integration coverage.
- Record any intentionally skipped coverage explicitly in the task summary.

## Unit vs Integration

- `unit`: mock-based or logic-only tests that do not require real DB persistence.
- `integration`: PostgreSQL-backed tests that open sessions, hit ORM queries, persist records, or validate database behavior.

## PostgreSQL Integration Rule

- `TEST_DATABASE_URL` is required for integration tests.
- Integration tests must not silently fall back to SQLite.
- Shared PostgreSQL fixtures should own transaction setup and rollback.
- Integration tests should not create their own ad hoc `SessionLocal()` fixtures when a shared test fixture exists.

## Relationship To `development/docs/testing/`

The files under `development/docs/testing/` remain the detailed reference set for test layout, commands, migration notes, and known status.

When a detailed testing document conflicts with this file, follow this file and update the detailed testing docs in the same task.
