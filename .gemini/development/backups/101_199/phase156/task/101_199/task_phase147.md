# Phase 147 Task

## Context

- The current codebase and recent manual-testing work surfaced a few documentation and helper-script mismatches.
- The most important remaining gaps were in manual testing guidance, especially around MMS size rules and AI-agent runtime entry points.
- The previously suggested `docs/current_status_summary.md` target does not exist in the active docs tree, so this phase focuses on the active files that are present.

## Goals

- Update active manual-testing docs so they match the current runtime behavior.
- Remove stale `Activity` tab assumptions from the smoke and regression helper scripts.
- Clarify that AI-agent manual runtime validation should use `ai-agent-panel` and `/ai-agent/api/*`, while `verify_responses.py` remains a direct service harness.
- Keep the phase limited to docs and manual-test helper assets.
