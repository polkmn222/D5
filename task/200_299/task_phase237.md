# Phase 237 Task

## Approved Scope
- Opportunity lookup parity for `model` only
- Opportunity object only
- Narrow safe lookup slice only:
  - search
  - select
  - preload
  - clear
  - submit ID

## Explicitly Out Of Scope
- `product`
- `asset`
- brand/model dependency behavior
- broader opportunity parity
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
