# Phase 70 Implementation

## Changes

- Updated `docs/agent.md` to lock the current top-level folder structure and define the repository-root `/.pytest_cache` as the only accepted pytest cache location.
- Updated `docs/workflow.md` to forbid casual structural reorganization and to treat nested pytest caches as accidental local state.
- Updated `test/README.md` to document the single-cache policy for local test runs.

## Notes

- This phase changes documentation only.
- No application code or test logic was modified.
