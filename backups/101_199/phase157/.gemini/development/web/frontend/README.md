# Web Frontend Guide

## Scope

- This folder owns the shared CRM templates and static assets.
- Shared templates live in `templates/`.
- Shared CSS and JavaScript live in `static/`.

## Canonical Docs

- Primary rules live in `/.gemini/development/docs/skill.md`.
- UI rules live in `/.gemini/development/docs/ui_standards.md`.
- Runtime structure lives in `/.gemini/development/docs/architecture.md`.
- Testing rules live in `/.gemini/development/docs/testing/`.

## Entrypoints

- `templates/base.html`: shared page shell and global UI hooks.
- `templates/detail_view.html`: shared detail template family reference.
- `static/css/`: shared styling.
- `static/js/`: shared interaction logic such as list views, lookup behavior, and bulk actions.

## Current Rules

- This folder covers shared CRM pages, not messaging-specific pages.
- Detail and list templates should follow the established shared product grammar.
- Editable detail pages use the shared inline-edit and pencil-icon patterns documented in `ui_standards.md`.
- Object-specific exceptions must be documented rather than silently diverging.

## Common Gotchas

- Messaging detail templates live under `web/message/frontend/`, not here.
- Changes to `base.html` or shared JS/CSS can affect many objects at once.
- When a page is intentionally read-only, do not force shared editable behavior just to satisfy an outdated assumption.

## Tests

- Shared UI tests live under `/.gemini/development/test/unit/ui/shared/`.
- Object-specific frontend expectations also appear under the relevant object unit-test folders.
