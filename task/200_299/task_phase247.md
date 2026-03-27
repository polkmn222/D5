## Phase 247 Task Record

### Scope

- Opportunity-only post-submit latency reduction for AI Agent chat-native form submit.
- Frontend-only first.
- Narrow scope only.

### Approved Direction

- After successful opportunity chat-form submit, keep appending the opportunity success/chat-card result below in chat.
- Do not automatically call the workspace open/fetch path after successful opportunity `OPEN_RECORD`.
- Keep the explicit `Open Record` action available in the opportunity chat card.
- Keep the downward ChatGPT-style flow.
- Keep lead behavior as-is from phase 245.
- Keep contact behavior as-is from phase 246.
- Keep all non-submit `OPEN_RECORD` flows unchanged in this phase.

### Constraints

- Do not broaden this beyond opportunity.
- Do not redesign the workspace model.
- Do not remove workspace compatibility entirely.
- Do not change the backend submit contract unless a blocker is found and reported first.
- Unit tests only.
- Manual testing is forbidden.

### Required Tests

1. Opportunity chat-form submit still appends the success/chat-card result.
2. Opportunity chat-form submit no longer calls `openAgentWorkspace(...)` after successful opportunity `OPEN_RECORD`.
3. Lead submit stays in the current no-auto-open behavior from phase 245.
4. Contact submit stays in the current no-auto-open behavior from phase 246.
5. Existing opportunity chat card actions remain available.
