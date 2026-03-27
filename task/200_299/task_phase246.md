## Phase 246 Task Record

### Scope

- Contact-only post-submit latency reduction for AI Agent chat-native form submit.
- Frontend-only first.
- Narrow scope only.

### Approved Direction

- After successful contact chat-form submit, keep appending the contact success/chat-card result below in chat.
- Do not automatically call the workspace open/fetch path after successful contact `OPEN_RECORD`.
- Keep the explicit `Open Record` action available in the contact chat card.
- Keep the downward ChatGPT-style flow.
- Keep lead behavior as-is from phase 245.
- Keep opportunity unchanged in this phase.
- Keep all non-submit `OPEN_RECORD` flows unchanged in this phase.

### Constraints

- Do not broaden this to opportunity.
- Do not redesign the workspace model.
- Do not remove workspace compatibility entirely.
- Do not change the backend submit contract unless a blocker is found and reported first.
- Unit tests only.
- Manual testing is forbidden.

### Required Tests

1. Contact chat-form submit still appends the success/chat-card result.
2. Contact chat-form submit no longer calls `openAgentWorkspace(...)` after successful contact `OPEN_RECORD`.
3. Lead submit stays in the current no-auto-open behavior from phase 245.
4. Opportunity submit still keeps the current workspace-open behavior.
5. Existing contact chat card actions remain available:
   - `Open Record`
   - `Edit`
   - `Delete`
