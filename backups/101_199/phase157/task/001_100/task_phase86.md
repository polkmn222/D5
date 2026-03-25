# Phase 86 Task

## Context

- The Lead list view crashed after the new list-view controls shipped.
- `crm.log` showed `Object of type Undefined is not JSON serializable` while rendering `leads/list_view.html`.

## Goals

- Remove the Lead list-view render crash.
- Keep the `All` and `Recently Viewed` controls working.
- Add regression coverage for missing list-view template context.
- Save phase-tagged documentation and code backups for the change.
