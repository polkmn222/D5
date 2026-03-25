# Phase 133 Task

## Context

- The user wants a full reset of the current CRM records and a fresh realistic dataset with unique names across the main CRM objects.
- Opportunity inline editing still needs a true Salesforce-style stage picklist and reliable save behavior for lookup plus renamed fields.
- `metadata.json` and the live database state both need a post-change consistency check after the new seed data is created.

## Goals

- Back up the current runtime data, clear the active CRM records, and regenerate 50 realistic records per core object family with meaningful linked lookups.
- Fix Opportunity inline editing so lookup fields and renamed fields save correctly, `Stage` edits use a picklist, and the path bar stays in sync.
- Re-verify `metadata.json` against the active schema and run focused unit tests for the changed UI and save logic.
