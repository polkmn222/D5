# Phase 235 Task

## Approved Scope
- Opportunity lookup parity for `contact` only
- Opportunity object only
- Narrow safe lookup slice only:
  - search
  - select
  - preload
  - clear
  - submit ID

## Explicitly Out Of Scope
- `brand`
- `model`
- `product`
- `asset`
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
