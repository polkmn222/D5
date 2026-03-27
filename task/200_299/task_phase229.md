# Phase 229 Task

- Scope: conversational UX polish for `lead`, `contact`, and `opportunity` only.
- Approved behavior:
  improve `MANAGE` / `OPEN_RECORD` / edit handling,
  use conversation context first,
  use a single selected record as a secondary signal,
  ask a narrow clarification if context and selection conflict,
  do not silently pick the wrong object.
- Constraints:
  no new objects,
  keep create/update/query contract unchanged,
  unit tests only,
  no manual testing.
