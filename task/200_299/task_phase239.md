# Phase 239 Task

## Approved Scope
- Remaining raw `OPEN_FORM` normalization cleanup only
- Scope limited to approved phase objects:
  - `lead`
  - `contact`
  - `opportunity`

## Target Cases
- `update lead <id>` with no fields
- `update contact <id>` with no fields
- `update opportunity <id>` with no fields
- older explicit edit/manage paths that may still internally produce raw `form_url`-only `OPEN_FORM`

## Constraints
- No new lookup slices
- No broader opportunity parity
- No unrelated UX redesign
- No modal reuse
- No slot-filling
- Keep the create/update/query contract unchanged
- Clean up carefully at the source without duplicating later rescue logic
- Unit tests only
- No manual testing
- Do not commit unless explicitly asked
- Do not push unless explicitly asked
