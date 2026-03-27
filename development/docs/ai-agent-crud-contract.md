# AI Agent CRUD Contract

## Purpose

This document defines the expected CRUD behavior contract for `development/ai_agent`.

## Scope

The main conversational CRM agent under `development/ai_agent` must support these objects:

- lead
- contact
- opportunity
- product
- asset
- brand
- model
- message_template

The mounted runtime must remain under `development/ai_agent`. Do not create a separate parallel agent framework outside this tree.

## Execution Model

The preferred execution order is:

1. parse request
2. resolve object
3. resolve action
4. normalize fields
5. execute the existing service
6. return a normalized UI response

Deterministic handling should be attempted before LLM fallback.

## Delivery Strategy

- Prefer object-by-object completion over tiny feature slices spread across many objects.
- When improving chat-native UX, finish the next smallest coherent gap for the current object before broadening to another object.
- Keep phases narrow, but prioritize user-visible completeness for the active object path.

## Service Reuse Rule

Reuse existing D5 services where possible:

- `development/web/backend/app/services/`
- `development/web/message/backend/services/`

Do not invent fields, IDs, SQL columns, or service behavior that the repository does not already support.

## Response Contract

### Create

Successful `CREATE` must return an `OPEN_RECORD`-style response for the newly created object.

The response should include:

- normalized intent indicating the record can be opened
- object type
- created record ID
- record open target for the UI
- user-facing text that matches the frontend response pattern

### Incomplete Create Requests

For incomplete create requests, the default D5 behavior is:

- enough required fields -> `CREATE` now and return `OPEN_RECORD`
- not enough required fields -> `OPEN_FORM`
- ambiguous mixed prompts -> ask a narrow clarification only when confidence is high; otherwise `OPEN_FORM`
- do not implement chat-first slot-filling unless explicitly requested by the user

This rule applies to the main conversational CRM agent under `development/ai_agent`.

### Minimum Required Fields For Deterministic Create

The current deterministic create minimums are:

- `lead`: `last_name` and `status`
- `contact`: `last_name` and `status`
- `opportunity`: `name`, `stage`, and `amount`

If these minimum fields are present with sufficient confidence, the agent should create the record directly and return `OPEN_RECORD`.

If these minimum fields are not present, the agent should prefer `OPEN_FORM`.

### Update

Successful `UPDATE` must return the refreshed record detail view for that object through an `OPEN_RECORD`-style response.

The response should represent the post-update state, not stale pre-update data.

### Query

Requests such as the following must return list-view-style results:

- `all leads`
- `show all contacts`
- `recent opportunities`

The query response should be compatible with the frontend list-view pattern and include pagination metadata when applicable.

### Manage / Open

`MANAGE`, `OPEN_RECORD`, and `OPEN_FORM` should behave consistently across supported objects.

At minimum:

- `MANAGE` should resolve the target record or form without object-specific drift
- `OPEN_RECORD` should point the UI at the correct detail target
- `OPEN_FORM` should point the UI at the correct create or edit form target

For approved chat-native objects, continuity should prefer the latest active chat area first and preserve workspace compatibility without letting the workspace steal visible focus.

## Ambiguous Or Unsupported Requests

If the request is ambiguous, unsupported, or too complex for deterministic handling:

- do not hallucinate a CRUD action
- do not hallucinate fields, IDs, or SQL
- do not fabricate success
- return a safe explanatory response or use LLM fallback only when appropriate

If the user intent cannot be safely resolved, the agent should ask for clarification or return a constrained safe response.

## Object-Specific Expectations

### Lead

- create success opens the new lead record
- update success opens the refreshed lead record
- `all leads` returns list-view-style results
- incomplete requests such as `create lead` use `OPEN_FORM` by design
- deterministic create requires `last_name` and `status`
- current chat-first continuity rollout includes submit-path continuity, non-submit `OPEN_RECORD` continuity, and selection `Open` continuity

### Contact

- create success opens the new contact record
- update success opens the refreshed contact record
- `all contacts` returns list-view-style results
- incomplete requests such as `create contact` use `OPEN_FORM` by design
- deterministic create requires `last_name` and `status`
- current chat-first continuity rollout includes submit-path continuity, non-submit `OPEN_RECORD` continuity, and selection `Open` continuity
- current contact chat cards expose `Open Record`, `Edit`, `Delete`, and `Send Message`

### Opportunity

- create success opens the new opportunity record
- update success opens the refreshed opportunity record
- `recent opportunities` and `all opportunities` return list-view-style results
- incomplete requests such as `create opportunity` use `OPEN_FORM` by design
- deterministic create requires `name`, `stage`, and `amount`
- current chat-first continuity rollout includes submit-path continuity, non-submit `OPEN_RECORD` continuity, and selection `Open` continuity
- current opportunity chat cards expose `Open Record`, `Edit`, `Delete`, and `Send Message`

### Product

- create success opens the new product record
- update success opens the refreshed product record
- `all products` returns list-view-style results
- current grouped-object rollout starts with product non-submit `OPEN_RECORD` continuity and selection `Open` continuity

### Asset

- create success opens the new asset record
- update success opens the refreshed asset record
- `all assets` returns list-view-style results
- current grouped-object rollout now includes asset non-submit `OPEN_RECORD` continuity and selection `Open` continuity

### Brand

- create success opens the new brand record
- update success opens the refreshed brand record
- `all brands` returns list-view-style results
- current grouped-object rollout now includes brand non-submit `OPEN_RECORD` continuity and selection `Open` continuity

### Model

- create success opens the new model record
- update success opens the refreshed model record
- `all models` returns list-view-style results
- current grouped-object rollout now includes model non-submit `OPEN_RECORD` continuity and selection `Open` continuity

### Message Template

- create success opens the new message template record
- update success opens the refreshed message template record
- `all message templates` returns list-view-style results
- current grouped-object rollout now includes message-template non-submit `OPEN_RECORD` continuity, selection `Open` continuity, safe image preview in chat cards, and `Use In Send Message` handoff through the existing messaging path

### Message Send

- first grouped-object history rollout starts with generic query/list support for `show messages` and `show recent messages`
- recipient, date-relative, and template-based filtering remain follow-up phases

## Frontend Compatibility Rule

The AI agent response should reuse established frontend response patterns so the UI can directly:

- open a record
- refresh a record
- open a form
- show query/list results

For approved lead, contact, and opportunity flows, the current continuity strategy is:

- submit success stays in the chat thread and does not auto-open the workspace
- non-submit `OPEN_RECORD` appends the newest result/card in chat first
- workspace compatibility remains available downstream
- selection-driven `Open` actions use chat-first continuity where rolled out for the object

For the current `SEND_MESSAGE` handoff flow, the continuity strategy is:

- handoff confirmation lands in the latest chat area first
- chat focus is preserved before the messaging workspace opens
- existing selection and template session handoff data remains the source of truth for the send page import behavior

## Current UI Entry Points That Still Use `OPEN_FORM` By Design

The following entry points intentionally still use `OPEN_FORM` when the request is incomplete:

- bare create prompts such as `create lead`, `create contact`, and `create opportunity`
- quick create actions that send the equivalent incomplete create prompt
- create requests that identify the object but do not provide the minimum deterministic required fields

This is expected behavior, not a regression.

Any future change to this contract must update this document and the corresponding tests in the same task.
