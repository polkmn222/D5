# Coverage Matrix

## Core CRM Objects

| Area | CRUD | List/Search | UI Actions | Integration |
| --- | --- | --- | --- | --- |
| Contacts | required | required | required | recommended |
| Leads | required | required | required | recommended |
| Opportunities | required | required | required | recommended |
| Assets | required | required | required | recommended |
| Products | required | required | required | recommended |
| Vehicle Specs / Models | required | required | recommended | optional |

## Shared Features

| Area | Unit | Integration | Manual |
| --- | --- | --- | --- |
| Lookup search | required | optional | optional |
| Inline edit / batch save | required | optional | optional |
| Table sorting / shared UI hooks | required | optional | optional |
| Messaging providers | required | recommended | optional |
| AI agent reasoning and context | required | recommended | optional |
| Provider-backed messaging delivery | optional | optional | required |

## Legacy Handling

- Keep phase-named tests out of core coverage reporting until they are rewritten under domain folders.
- Track archived or historically useful tests in `unit/legacy/` rather than mixing them into core object coverage.
