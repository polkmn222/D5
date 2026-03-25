# Phase 136 Task

## Context

- The current delete flow still behaves like a soft delete on most CRM objects, which leaves stale rows in the database and allows deleted records to leak back into lookup flows.
- Lookup saves can fail when a cleared lookup field submits an empty string instead of a nullable foreign-key value, and stale recent-lookup cache can reintroduce deleted records in the UI.
- Messaging also needs stronger template/message lookup guarantees so send records only reference active templates and deleted templates do not linger as broken related links.

## Goals

- Convert user-facing record deletion flows to hard deletes with explicit related-record cleanup for the supported CRM object graph.
- Harden lookup search, recent lookup rendering, inline save, batch save, and modal form persistence so deleted values never appear and cleared lookups save as `NULL` safely.
- Repair message/template lookup integrity and add focused unit coverage for lookup filtering, nullable lookup saves, and cascade deletion behavior.
