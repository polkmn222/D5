Phase 261 Task Record

Scope
- Send-side handoff continuity bundle.
- Keep scope limited to chat-first `SEND_MESSAGE` continuity and existing sessionStorage handoff preservation.
- Align template `Use In Send Message` and selection-triggered `Send Message` with the same chat-first handoff behavior.

Approvals
- Frontend-first only.
- Do not redesign the compose screen.
- Do not implement send-history / query support in this phase.

Out Of Scope
- Send-history / query / inspection support.
- Recipient/date/template query semantics.
- Provider/integration redesign.
- Actual delivery flow redesign.
- Recipient-resolution redesign.
- Send-page form redesign.
- Image upload/storage changes.
- Template editor changes.

Constraints
- Unit tests mandatory.
- DOM-level UI tests required for changed UI behavior.
- No manual testing.
- No SQLite.
