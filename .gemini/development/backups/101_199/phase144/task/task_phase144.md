# Phase 144 Task

## Context

- Asset, Lead, Opportunity, and Message detail flows still have gaps around lookup edit, lookup clear, and related refresh behavior.
- Message detail has transitioned from a read-only exception to a surface that now needs standard object-level `Edit` and `Delete` actions.
- Lead conversion is intermittently hanging in the modal flow, and Lead lookup field presentation still looks different from the other CRM objects.

## Goals

- Fix lookup clear and refill behavior so related data returns correctly after a lookup is reattached.
- Make Lead and Opportunity lookup editing work reliably from both the top-level `Edit` action and field pencil flow.
- Add message-detail `Edit` and `Delete` actions, make message lookup clears persist, and align the messaging docs/tests with the editable runtime contract.
- Remove the lead conversion infinite-loading behavior and unify Lead lookup field UI with the standard detail grammar.
