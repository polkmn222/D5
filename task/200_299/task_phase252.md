## Phase 252 Task

### Title
Contact-only selection/table Open continuity

### Approved Scope
- Frontend-only first
- Narrow scope only
- Contact selection/table `Open` should route through chat first
- Reuse the existing `Manage contact <id> -> OPEN_RECORD` continuity path
- Do not directly open the workspace from the contact selection-open trigger

### Must Preserve
- Lead selection `Open` unchanged
- Opportunity selection `Open` unchanged from Phase 251
- Submit-path no-auto-open behavior unchanged
- Non-submit `OPEN_RECORD` preserved-focus behavior unchanged
- Workspace compatibility where already needed downstream

### Documentation Requirements
- Update the relevant markdown guidance so it reflects the object-by-object implementation strategy
- Document the UI-phase testing rule: unit tests plus narrow DOM-level UI tests
- Document the non-UI testing rule: unit tests only
- Document that browser automation is not used unless explicitly approved
- Document the chat-first continuity rollout for approved objects

### Required Tests
- Focused unit coverage for contact selection-open routing and unchanged neighboring object behavior
- Narrow DOM-level UI coverage for contact selection-open continuity only
- No browser automation
- No manual testing
