# Known Test Status

This file tracks tests that are known to have special behavior, skip conditions, or were updated for specific reasons.

## Phase 169 Changes

| Test | Status | Reason |
|---|---|---|
| `test_lead_update_returns_view_card` | Updated | Changed from `process_query` (LLM-path, non-deterministic) to `_execute_intent` (deterministic). LLM may classify `update lead TEST_FLOW_LEAD ...` differently based on model used. Core behavior is now tested reliably. |

## Current Full Unit Reference

- Command: `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit -rs -q`
- Last reviewed status: `337 passed`

## Current State

- There are no currently recorded failing or skipped unit tests in the canonical full-suite run.
- The mismatches documented in phase 135 and early phase 136 were resolved by aligning tests and test docs to the current runtime contract without changing runtime code.

## Historical Notes

- Messaging UI tests now account for the split template roots under `web/message/frontend/templates/`.
- The message-send detail page is tested as a non-inline-edit exception: it exposes object-level `Edit` / `Delete` actions without shared pencil-based inline editing.
- SMS template subject expectations, AI selection payload normalization, and direct-call router signatures are now reflected in the unit suite.

## Usage Rule

- Use this file to document known test mismatches while docs, tests, and runtime behavior are being brought back into alignment.
- Do not treat entries here as permanent waivers; remove or update them when the runtime or tests are corrected.
