Phase 262 Task Record

Scope
- Send-history query/list first.
- Keep scope limited to generic history queries for the `message_send` surface:
  - `show messages`
  - `show recent messages`

Approvals
- Query/list only first.
- No send detail behavior in this phase.
- No recipient/date/template filtering in this phase.
- Backend-only if possible.

Out Of Scope
- `show messages sent to A`
- `show messages sent yesterday`
- `show sends using this template`
- `show sent message items for a specific recipient`
- Recipient-name filtering
- Date-relative filtering
- Template-based filtering
- Message detail/open continuity changes
- Compose/handoff redesign
- Provider/integration behavior
- Image/template storage behavior

Constraints
- Unit tests mandatory.
- No DOM-level UI tests because this phase stays backend/query-only.
- No manual testing.
- No SQLite.
