## Phase 255 Task

### Title
Approved-object-wide delete-confirmation continuity and scroll polish

### Approved Scope
- Applies only to lead, contact, and opportunity
- Frontend-only first
- Narrow scope only
- Card-triggered `Delete` should append the confirmation in the latest chat area and scroll it into view
- Selection/table `Delete` should append the confirmation in the latest chat area and scroll it into view
- Keep the delete flow chat-native in visible behavior

### Must Preserve
- No backend delete behavior changes
- No pending-delete model redesign
- No workspace-open behavior from this continuity polish
- `Open` and `Edit` continuity unchanged
- Submit continuity unchanged
- Non-submit `OPEN_RECORD` continuity unchanged

### Required Tests
- Focused unit coverage for card and selection delete confirmation scroll behavior
- Narrow DOM-level UI coverage for chat-native delete confirmation continuity
- No browser automation
- No manual testing
