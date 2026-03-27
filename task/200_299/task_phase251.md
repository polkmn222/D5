## Phase 251 Task

### Title
Opportunity-only selection/table Open continuity

### Approved Scope
- Frontend-only first
- Narrow scope only
- Opportunity selection/table `Open` should route through chat first
- Reuse the existing chat-native `Manage opportunity <id>` to `OPEN_RECORD` continuity path
- Do not directly open the workspace from the opportunity selection-open trigger

### Must Preserve
- Lead selection `Open` behavior unchanged
- Contact selection `Open` unchanged
- Submit-path no-auto-open behavior unchanged
- Non-submit `OPEN_RECORD` preserved-focus behavior unchanged
- Workspace compatibility where already needed downstream

### Required Tests
- Unit tests for selection-open routing and unchanged neighboring behavior
- Narrow DOM-level UI tests for opportunity selection-open continuity only
- No browser automation
- No manual testing
