# Phase 241 Task

## Approved Scope
- Approved-object behavior parity cleanup only
- Scope limited to:
  - `lead`
  - `contact`
  - `opportunity`

## Behavior Parity Targets
- `OPEN_RECORD` consistency
- `MANAGE` consistency
- post-submit transition consistency
- record summary/card consistency

## Explicitly Out Of Scope
- scalar field parity
- lookup field parity
- validation redesign
- new objects
- new lookup slices
- broader UI redesign

## Constraints
- Keep frontend behavior minimal.
- Keep the create/update/query contract unchanged.
- Reuse the existing chat-native form model.
- Unit tests only.
- No manual testing.
- Do not commit unless explicitly asked.
- Do not push unless explicitly asked.
