# Phase 67 Task

## Context

Phase 66 documentation cleanup was already in progress, so Phase 67 was selected as the next unused phase number.

## Goals

- Remove remaining SQLite-specific assumptions from active unit tests and manual verification helpers.
- Move manual verification scripts to a PostgreSQL-backed `TEST_DATABASE_URL` workflow.
- Refresh `docs/spec.md` and `docs/ui_standards.md` so they reflect the current detail-view patterns, AI mount expectations, and phase tracking rules.
- Back up all touched files under `.gemini/development/backups/phase67/` before editing.
