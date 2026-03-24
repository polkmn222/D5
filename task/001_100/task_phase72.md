# Phase 72 Task

## Context

The repository still had a nested pytest cache under `.gemini/development`, a root-level `SESSION_HANDOFF.md`, and multiple backup files that were not stored in clean phase-relative locations.

## Goals

- Keep only the repository-root `/.pytest_cache`.
- Move `SESSION_HANDOFF.md` into `docs/` and clarify its relationship to canonical documentation.
- Add the rule that new project-level markdown files belong in `docs/`.
- Reorganize loose backup files into their proper phase folders and relative paths.
