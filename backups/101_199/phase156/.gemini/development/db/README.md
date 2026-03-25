# Database Guide

## Scope

- This folder owns database configuration, ORM models, and seed helpers.
- Connection setup lives in `database.py`.
- ORM entities live in `models.py`.
- Seed helpers live in `seeds/`.

## Canonical Docs

- Runtime structure lives in `/.gemini/development/docs/architecture.md`.
- Deployment and environment expectations live in `/.gemini/development/docs/deployment.md`.
- Testing rules live in `/.gemini/development/docs/testing/`.

## Current Rules

- PostgreSQL is the active runtime database.
- `DATABASE_URL` is required for real runtime behavior.
- Shared audit fields are defined at the model layer, but startup auto-heal assumptions should be documented carefully and not overstated.
- Seed helpers should support controlled dev and test workflows without becoming production migration substitutes.

## Common Gotchas

- Do not assume every schema mismatch is fixed automatically at startup.
- Be careful with destructive local scripts and old backup helpers.
- Keep model changes, docs, and tests aligned in the same phase.

## Tests

- Model and database-adjacent tests appear across `/.gemini/development/test/unit/`.
- Manual test setup helpers live under `/.gemini/development/test/manual/data_setup/`.
