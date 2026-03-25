# Phase 137 HTTP Manual Check

## Scope

- Date: 2026-03-24
- Environment: local app started with `uvicorn api.index:app --host 127.0.0.1 --port 8011`
- Exclusions: `Send Message` flows and `AI Agent` flows were intentionally excluded.
- Method: HTTP response inspection only from the local environment; no browser-driven clicking, visual comparison, or destructive form submission was performed.

## Stored Artifacts

- Summary markdown: `test/manual/evidence/phase137/http_manual_check.md`
- Server log for the earlier messaging-oriented local validation run: `test/manual/evidence/phase137/logs/manual_test_server_8010.log`
- Server log for the non-messaging local validation run: `test/manual/evidence/phase137/logs/manual_test_server_8011.log`
- Storage method used in this phase:
  - Start the local app on a dedicated port.
  - Capture stdout/stderr to a log file.
  - Save the run summary as markdown in the matching phase folder.
  - Keep related logs in the same phase folder under `logs/`.

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

## Follow-Up Notes

- This pass did not verify live browser interactions such as clicking tabs, saving inline edits, sorting tables, opening `Setup` popovers, or performing create/update/delete submissions.
- No runtime code was changed during this check.
