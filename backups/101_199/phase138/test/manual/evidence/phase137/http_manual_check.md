# Phase 137 HTTP Manual Check

## Scope

- Date: 2026-03-24
- Environment: local app started with `uvicorn api.index:app --host 127.0.0.1 --port 8011`
- Exclusions: `Send Message` flows and `AI Agent` flows were intentionally excluded.
- Method: HTTP response inspection only from the local environment; no browser-driven clicking, visual comparison, or destructive form submission was performed.

## Routes Verified

### Dashboard and list pages

- `/` -> `200`
- `/contacts` -> `200`
- `/leads` -> `200`
- `/opportunities` -> `200`
- `/products` -> `200`
- `/assets` -> `200`
- `/vehicle_specifications` -> `200`
- `/models` -> `200`

### Representative modal/form routes

- `/contacts/new` and `/contacts/new?id=003MWZ6s3CBO0NuYRL` -> `200`
- `/leads/new` and `/leads/new?id=00QCP38jUwhYHG42IO` -> `200`
- `/opportunities/new` and `/opportunities/new?id=006Rl6OnlSxr1MjISI` -> `200`
- `/products/new` and `/products/new?id=01tyZfjnDZ14PGBQY2` -> `200`
- `/assets/new` and `/assets/new?id=02iVrH4aYV5WrmkIZC` -> `200`

### Search endpoints

- `/search?q=Jiho&type=all` returned HTML containing `Jiho Park`
- `/api/search/suggestions?q=Jiho&type=all` returned data containing `003MWZ6s3CBO0NuYRL`
- `/lookups/search?q=Jiho&type=Contact` returned data containing `Jiho Park`

## Detail Pages Verified

### Contact

- Route: `/contacts/003MWZ6s3CBO0NuYRL`
- Found: `Details`, `Related`, `Edit`, `Delete`, `sf-pencil-icon`, `toggleInlineEdit`, `toggleLookupEdit`

### Lead

- Route: `/leads/00QCP38jUwhYHG42IO`
- Found: `Details`, `Related`, `Edit`, `Delete`, `sf-pencil-icon`, `toggleInlineEdit`, `toggleLookupEdit`

### Opportunity

- Route: `/opportunities/006Rl6OnlSxr1MjISI`
- Found: `Details`, `Related`, `Edit`, `Delete`, `sf-pencil-icon`, `toggleInlineEdit`, `toggleLookupEdit`

### Product

- Route: `/products/01tyZfjnDZ14PGBQY2`
- Found: `Details`, `Related`, `Edit`, `Delete`, `sf-pencil-icon`, `toggleInlineEdit`, `toggleLookupEdit`

### Asset

- Route: `/assets/02iVrH4aYV5WrmkIZC`
- Found: `Details`, `Related`, `Edit`, `Delete`, `sf-pencil-icon`, `toggleInlineEdit`, `toggleLookupEdit`

## Shared UI Markers Observed

- List pages for Contacts, Leads, Opportunities, Products, Assets, Vehicle Specifications, and Models all returned `Setup`, `New`, `Recently Viewed`, `Pin`, `table`, and `search` markers in the HTML.
- Representative detail pages returned inline-edit and lookup-edit hooks for the non-messaging object families checked above.

## Suspicious Or Follow-Up Notes

- The representative non-messaging detail pages checked in this pass exposed `Details` and `Related`, but not `Activity` in the returned HTML. This may be expected for the current runtime, but it does not fully match the wording in `docs/testing/manual_checklist.md` that mentions `Details`, `Related`, and `Activity`.
- This pass did not verify live browser interactions such as clicking tabs, saving inline edits, sorting tables, opening `Setup` popovers, or performing create/update/delete submissions.
- No runtime code was changed during this check.
