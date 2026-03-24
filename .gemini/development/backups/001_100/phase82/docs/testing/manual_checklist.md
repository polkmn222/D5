# Manual Testing Checklist

## Smoke Checklist

- App starts with `./run_crm.sh` and dashboard loads.
- Top-level navigation opens the expected object pages.
- Global search and one representative lookup search return usable results.
- One representative `Contact` create flow succeeds.
- One representative `Lead` update flow succeeds.
- One representative `Opportunity` delete or soft-delete flow succeeds.
- Detail page tabs and shared action buttons render correctly.

## Core CRM Regression Checklist

### Contacts

- Create a contact.
- Open the detail page.
- Update a field with inline edit.
- Verify list/detail consistency.
- Delete or soft-delete the record.

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

## Optional Domain Checklists

- Messaging: template selection, send flow, duplicate handling, attachments
- AI agent: chat flow, selection context, pagination, reset, template handoff

Run these only when those domains are in scope.
