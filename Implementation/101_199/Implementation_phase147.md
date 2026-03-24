# Phase 147 Implementation

## Changes

- Updated `/.gemini/development/docs/testing/manual_checklist.md` to split MMS guidance between the 500KB upload/template path and the 200KB Solapi send path.
- Updated `/.gemini/development/docs/testing/manual_runbook.md` to describe the actual AI-agent runtime entry points and to reclassify `verify_responses.py` as a service-level harness rather than the primary manual runtime check.
- Updated `/.gemini/development/test/manual/smoke/smoke_checklist.py` and `/.gemini/development/test/manual/regression/regression_checklist.py` to remove stale `Activity` tab assumptions and point AI manual testing toward `ai-agent-panel` and `/ai-agent/api/*`.
- Updated `/.gemini/development/test/manual/ai_agent/README.md` and `/.gemini/development/test/manual/ai_agent/verify_responses.py` to explain the difference between direct-service debugging and mounted runtime validation.
- Stored pre-change copies of the edited files under `/.gemini/development/backups/phase147/`.

## Verification

- Documentation and helper-script phase only; no runtime application code was changed.
- The phase intentionally skipped the previously suggested `docs/current_status_summary.md` item because that file does not exist in the active docs tree.
