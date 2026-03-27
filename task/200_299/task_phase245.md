## Phase 245 Task Record

### Scope

- Lead-only post-submit latency reduction for AI Agent chat-native form submit.
- Frontend-only first.
- Narrow scope only.

### Approved Direction

- After successful lead chat-form submit, keep appending the lead success/chat-card result below in chat.
- Do not automatically call the workspace open/fetch path after successful lead `OPEN_RECORD`.
- Keep the explicit `Open Record` action available in the lead chat card.
- Keep the downward ChatGPT-style flow.
- Keep contact and opportunity unchanged in this phase.
- Keep all non-submit `OPEN_RECORD` flows unchanged in this phase.

### Constraints

- Do not broaden this to contact or opportunity.
- Do not redesign the workspace model.
- Do not remove workspace compatibility entirely.
- Do not change the backend submit contract unless a blocker is found and reported first.
- Unit tests only.
- Manual testing is forbidden.

### Required Tests

1. Lead chat-form submit still appends the success/chat-card result.
2. Lead chat-form submit no longer calls `openAgentWorkspace(...)` after successful `OPEN_RECORD`.
3. Non-lead chat-form submit paths still keep the current workspace-open behavior.
4. Existing lead chat card actions remain available:
   - `Open Record`
   - `Edit`
   - `Delete`
   - `Send Message`

### Separate Reported Risk

- The workspace header markup references `triggerWorkspaceEdit()` and `triggerWorkspaceDelete()`, but this issue is explicitly out of scope for phase 245.
