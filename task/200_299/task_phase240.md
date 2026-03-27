# Phase 240 Task

## Approved Scope
- Opportunity lookup parity for `asset` only
- Opportunity object only
- Narrow safe lookup slice only:
  - search
  - select
  - preload
  - clear
  - submit ID

## Explicitly Out Of Scope
- general opportunity parity
- linked amount/default pricing behavior
- asset-driven auto-sync behavior
- broader dependency logic
- modal reuse
- slot-filling

## Constraints
- Keep the create/update/query contract unchanged.
- Keep the frontend behavior minimal.
- Reuse the existing generic chat-native lookup pattern.
- Unit tests only.
- No manual testing.
- Do not commit unless explicitly asked.
- Do not push unless explicitly asked.
