# Manual Testing Checklist

## Smoke Checklist

- App starts with `./run_crm.sh` and dashboard loads.
- Top-level navigation opens the expected object pages such as `/contacts`, `/leads`, `/opportunities`, and `/products`.
- Global search and one representative lookup search return usable results.
- One representative `Contact` create flow succeeds from `/contacts`.
- One representative `Lead` update flow succeeds from `/leads`.
- One representative `Opportunity` delete or soft-delete flow succeeds from `/opportunities`.
- Detail page tabs such as `Details` and `Related`, plus shared action buttons, render correctly.

## Core CRM Regression Checklist

### Contacts

- Create a contact.
- Verify the list view loads without agent/runtime errors.
- Use `Setup` to open saved list view controls, pin a view, and switch between at least two views.
- Open the detail page.
- Update a field with inline edit.
- Verify list/detail consistency.
- Delete or soft-delete the record.
- Verify at least one contact-related lookup or related-list surface.

### Leads

- Create a lead.
- Verify the list view loads without agent/runtime errors.
- Use `Setup` to save or clone a lead list view, then confirm pin and recent-view behavior.
- Update status and key fields.
- Verify lookup and search visibility.
- Convert the lead where supported.
- Confirm downstream records appear as expected.

### Opportunities

- Create an opportunity.
- Verify the list view loads without agent/runtime errors.
- Use `Setup` to save or clone an opportunity list view, then confirm pin and recent-view behavior.
- Update amount or stage.
- Verify dashboard or list visibility.
- Confirm sorting and detail-page actions.

### Assets

- Create or edit an asset from `/assets`.
- Verify the list view loads without agent/runtime errors.
- Open `Setup`, save a custom asset list view, and verify pin / recent-view behavior.
- Verify VIN or related fields.
- Confirm detail-page rendering and related links.

### Products

- Create or edit a product from `/products`.
- Verify the list view loads without agent/runtime errors.
- Open `Setup`, save a custom product list view, and verify pin / recent-view behavior.
- Verify brand/model associations.
- Confirm list/detail rendering.

### Assets, Products, Vehicle Specs, Models

- Create a record for each object family under review.
- Verify each list page loads and saved list view controls open without runtime errors.
- Save or clone one representative list view for Brands and Models and verify pin / recent-view behavior.
- Verify related lookups resolve correctly.
- Update a representative field.
- Confirm list/detail rendering and delete behavior.

## Shared UI Regression Checklist

- Tabs render and switch correctly.
- Inline edit opens, saves, and cancels correctly.
- Batch edit and batch save work as expected.
- Table sorting hooks behave correctly.
- Bulk action controls appear only when valid selections exist.
- Salesforce-style list view controls render correctly, including `Setup`, `Pin`, filter conditions, visible fields, and recent-view switching.
- Messaging detail pages are checked against their active contract: `message_templates` detail remains editable, while `messages` detail is currently read-only and should not show pencil icons.

## Messaging Regression Checklist

- `/messaging/ui` loads and shows recipient, template, and recommendation surfaces.
- `/message_templates` list and detail pages render from the messaging template tree without missing-template errors.
- `Message Template` detail supports edit and image-management actions where applicable.
- `Message Send` detail opens with `Details` and `Related` tabs and remains read-only.
- If MMS is in scope, verify JPG-only and 500KB upload guidance appears for the template/upload path.
- If `MESSAGE_PROVIDER=solapi`, also verify operational guidance makes it clear that real Solapi sends require JPG images at or under 200KB.

## Manual Helper Notes

- `test/manual/smoke/smoke_checklist.py` supports interactive execution, `--print-only`, and markdown report output.
- `test/manual/regression/regression_checklist.py` supports interactive execution, `--print-only`, and markdown report output.
- Reports are saved under `test/manual/evidence/` unless `--no-save` is used.
- Organize ad hoc manual notes and server logs under a phase folder such as `test/manual/evidence/phase137/`.
- Store the main summary as markdown and place raw server logs in `test/manual/evidence/phase137/logs/`.
- If failures are recorded, a failed-item rerun checklist is generated automatically in the same evidence folder.

## Optional Domain Checklists

- Messaging: template selection, send flow, duplicate handling, attachments
- AI agent: `ai-agent-panel` loading, `/ai-agent/api/chat`, selection context, pagination, reset, and template handoff

Run these only when those domains are in scope.
