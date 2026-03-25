Test assets are centralized here.

- `unit/` contains active unit tests, including `unit/ai_agent/`.
- `integration/` contains integration tests.
- `manual/` contains legacy or manual-only verification scripts and helpers that should not be part of the default pytest run.
- `databases/` contains local database fixtures and scratch data used by tests and manual verification scripts.
- `docs/` contains archived test-specific notes from earlier phases.

Canonical testing guidance now lives under `.gemini/development/docs/testing/`.

Manual scripts should target `TEST_DATABASE_URL` for PostgreSQL-backed verification instead of relying on SQLite scratch databases.

Before planning or running unit tests, review the canonical testing docs under `.gemini/development/docs/testing/`.

Pytest cache policy:

- Use only `.gemini/development/.pytest_cache`.
- Do not keep `.pytest_cache` at the repository root, under `.gemini/`, or in any other duplicate location.
- Do not commit any pytest cache directory to git.
