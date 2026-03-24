# Testing Strategy

## Goal

Make unit testing more thorough by organizing tests around domain ownership, CRUD coverage, shared UI behaviors, and explicit runtime boundaries.

## Target Structure

```text
test/
  unit/
    crm/
      contacts/
      leads/
      opportunities/
      assets/
      products/
      vehicle_specs/
      shared/
    messaging/
      providers/
      templates/
      router/
      ui/
    ai_agent/
      backend/
      frontend/
    ui/
      shared/
      dashboard/
      lookup/
      tables/
    search/
    legacy/
  integration/
    crm/
    messaging/
    ai_agent/
  manual/
```

## Organization Rules

- Keep unit tests focused on one object, service family, or shared UI behavior per file.
- Keep messaging and AI agent tests isolated from core CRM object coverage.
- Move phase-named or history-named tests into `unit/legacy/` until they are rewritten or retired.
- Prefer shared fixtures and factories over inline setup duplication.
- Keep canonical testing rules in `docs/testing/` and keep `test/docs/` archived.

## CRUD Coverage Standard

For each core object family, aim to cover:

1. create
2. read/detail lookup
3. update
4. delete or soft delete
5. list/search/filter behavior
6. key UI actions tied to that object

## Execution Layers

- `unit`: isolated logic and template-structure verification.
- `integration`: app, router, DB, and multi-service verification.
- `manual`: provider-dependent or human-observed checks.
