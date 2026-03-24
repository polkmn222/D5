# Phase 79 Task

## Context

Manual testing needed a canonical plan, a clearer folder layout, and a separation between reusable helpers and stale legacy scripts.

## Goals

- Create canonical manual-testing docs under `.gemini/development/docs/testing/`.
- Reorganize `test/manual/` into smoke, regression, data setup, active AI-agent, and legacy areas.
- Classify old `tmp_system` scripts into reusable or legacy buckets.
- Document the dedicated PostgreSQL test DB and reset workflow for manual testing.
