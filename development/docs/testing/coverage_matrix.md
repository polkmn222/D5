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

## Shared Web CRM Surfaces

| Area | Unit / DOM Contract | Integration | Notes |
| --- | --- | --- | --- |
| CRUD modal/detail/trash behavior | required | optional | Covers create/edit modal routes, detail actions, and recycle-bin restore/permanent-delete behavior. |
| Buttons / user-triggered actions | required | optional | Covers shared New, Edit, Delete, Convert, Restore, View All, bulk delete, and list-view action controls where applicable. |
| List view contracts | required | optional | Covers shared list shells, selection, bulk-action hooks, list-view setup controls, search hooks, and persisted-view affordances. |
| Related list / detail related behavior | required | optional | Covers related-list page contracts and detail-view related-card actions and empty states. |
| Trash / recycle-bin router and DOM behavior | required | optional | Covers trash router redirects, recycle-bin search/windowing, empty state, and load-more indicator behavior. |
| Empty / loading states | required where applicable | optional | Covers list skeletons, empty-state contracts, and trash loading indicators for shared web views. |

## Shared Features

| Area | Unit | Integration | Manual |
| --- | --- | --- | --- |
| Lookup search | required | optional | optional |
| Inline edit / batch save | required | optional | optional |
| Table sorting / shared UI hooks | required | optional | optional |
| Shared CRM list/detail/related/trash DOM contracts | required | optional | optional |
| Shared CRM bulk-action JS behavior | required | optional | optional |
| Messaging providers | required | recommended | optional |
| AI agent reasoning and context | required | recommended | optional |
| Provider-backed messaging delivery | optional | optional | required |

## Coverage Notes

- Shared inline-edit coverage is required for object families that still use the shared editable detail pattern.
- Read-only detail pages, including the current message-send detail surface, should be covered by explicit read-only UI expectations instead of pencil-icon assertions.
- Messaging template and message-send UI tests must resolve templates from the active `web/message/frontend/templates/` tree when applicable.

## Legacy Handling

- Keep phase-named tests out of core coverage reporting until they are rewritten under domain folders.
- Track archived or historically useful tests in `unit/legacy/` rather than mixing them into core object coverage.
