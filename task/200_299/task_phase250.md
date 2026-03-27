## Phase 250 Task Record

### Scope

- Opportunity-only non-submit `OPEN_RECORD` continuity and scroll polish.
- Frontend-only first.
- Narrow scope only.

### Approved Direction

- Keep the newest opportunity result/card visible in the latest chat area.
- Do not let the workspace steal visible focus for opportunity non-submit `OPEN_RECORD`.
- Preserve workspace compatibility.
- Keep lead behavior unchanged from phase 248.
- Keep contact behavior unchanged from phase 249.
- Keep submit-path behavior unchanged from earlier phases.

### Target Flows

- Opportunity prompt-driven open/manage flows that resolve to `OPEN_RECORD`.
- Opportunity card `Open Record` actions that round-trip through chat.
- Opportunity selection/table `Open` flows if they already route through the same opportunity `OPEN_RECORD` path.
- `show/open the opportunity I just created` style flows when they resolve to opportunity `OPEN_RECORD`.

### Constraints

- No backend contract changes.
- No opportunity field or lookup parity work.
- No broader opportunity UI redesign.
- No multi-object continuity rewrite.
- No submit-path changes from earlier phases.
- Unit tests plus narrow DOM-level UI tests only.
- No browser automation.
- Manual testing is forbidden.

### Required Tests

1. Opportunity non-submit `OPEN_RECORD` appends the chat result/card before any workspace-focus effect.
2. Opportunity non-submit `OPEN_RECORD` uses preserved chat focus behavior.
3. Lead non-submit `OPEN_RECORD` remains unchanged from phase 248.
4. Contact non-submit `OPEN_RECORD` remains unchanged from phase 249.
5. Submit-path no-auto-open behavior for lead/contact/opportunity remains unchanged.
6. DOM-level continuity tests cover opportunity append order, opportunity preserved chat focus, and prompt/button-triggered opportunity action continuity.
