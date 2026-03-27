# Phase 242 Task

## Approved Scope
- Tighten the remaining lead-specific card inconsistency only
- Preserve the lead-specific card model
- Keep scope limited to the approved objects context:
  - `lead`
  - `contact`
  - `opportunity`
- Focus implementation primarily on lead

## Behavior Parity Targets
- action naming and ordering
- hint style
- subtitle/title conventions
- post-open/update wording

## Explicitly Out Of Scope
- full parity
- scalar field parity
- lookup field parity
- validation redesign
- converting lead into the generic `record_paste` model
- broader UI redesign

## Constraints
- Keep frontend behavior minimal.
- Keep the create/update/query contract unchanged.
- Do not remove useful lead-specific behavior.
- Unit tests only.
- No manual testing.
- Do not commit unless explicitly asked.
- Do not push unless explicitly asked.
