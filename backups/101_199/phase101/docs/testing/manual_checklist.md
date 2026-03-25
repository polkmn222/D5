# Manual Testing Checklist

## Smoke Checklist

- App starts with `./run_crm.sh` and dashboard loads.
- Top-level navigation opens the expected object pages such as `/contacts`, `/leads`, `/opportunities`, and `/products`.
- Global search and one representative lookup search return usable results.
- One representative `Contact` create flow succeeds from `/contacts`.
- One representative `Lead` update flow succeeds from `/leads`.
- One representative `Opportunity` delete or soft-delete flow succeeds from `/opportunities`.
- Detail page tabs such as `Details`, `Related`, and `Activity`, plus shared action buttons, render correctly.

## Core CRM Regression Checklist

### Contacts

- Create a contact.
- Open the detail page.
- Update a field with inline edit.
- Verify list/detail consistency.
- Delete or soft-delete the record.
- Verify at least one contact-related lookup or related-list surface.

### Leads

- Create a lead.
- Update status and key fields.
- Verify lookup and search visibility.
- Convert the lead where supported.
- Confirm downstream records appear as expected.

### Opportunities

- Create an opportunity.
- Update amount or stage.
- Verify dashboard or list visibility.
- Confirm sorting and detail-page actions.

### Assets

- Create or edit an asset from `/assets`.
- Verify VIN or related fields.
- Confirm detail-page rendering and related links.

### Products

- Create or edit a product from `/products`.
- Verify brand/model associations.
- Confirm list/detail rendering.

### Assets, Products, Vehicle Specs, Models

- Create a record for each object family under review.
- Verify related lookups resolve correctly.
- Update a representative field.
- Confirm list/detail rendering and delete behavior.

## Shared UI Regression Checklist

- Tabs render and switch correctly.
- Inline edit opens, saves, and cancels correctly.
- Batch edit and batch save work as expected.
- Table sorting hooks behave correctly.
- Bulk action controls appear only when valid selections exist.

## Manual Helper Notes

- `test/manual/smoke/smoke_checklist.py` supports interactive execution, `--print-only`, and markdown report output.
- `test/manual/regression/regression_checklist.py` supports interactive execution, `--print-only`, and markdown report output.
- Reports are saved under `test/manual/evidence/` unless `--no-save` is used.
- If failures are recorded, a failed-item rerun checklist is generated automatically in the same evidence folder.

## Optional Domain Checklists

- Messaging: template selection, send flow, duplicate handling, attachments
- AI agent: chat flow, selection context, pagination, reset, template handoff

Run these only when those domains are in scope.
