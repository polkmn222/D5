## Phase 249 Task Record

### Scope

- Contact-only non-submit `OPEN_RECORD` continuity and scroll polish.
- Frontend-only first.
- Narrow scope only.

### Approved Direction

- Keep the newest contact result/card visible in the latest chat area.
- Do not let the workspace steal visible focus for contact non-submit `OPEN_RECORD`.
- Preserve workspace compatibility.
- Keep submit-path behavior unchanged.
- Keep lead behavior unchanged from phase 248.
- Keep opportunity behavior unchanged in this phase.

### Target Flows

- Contact prompt-driven open/manage flows that resolve to `OPEN_RECORD`.
- Contact card `Open Record` actions that round-trip through chat.
- Contact selection/table `Open` flows if they route through the same contact `OPEN_RECORD` path.
- `show/open the contact I just created` style flows when they resolve to contact `OPEN_RECORD`.

### Constraints

- Do not bundle new contact card actions such as `Send Message`.
- Do not change backend contracts.
- Do not change contact edit-form model behavior.
- Do not broaden to broad non-lead workspace behavior changes.
- Do not perform a multi-object continuity rewrite.
- Unit tests plus narrow DOM-level UI tests only.
- No browser automation.
- Manual testing is forbidden.

### Required Tests

1. Contact non-submit `OPEN_RECORD` appends the chat result/card before any workspace-focus effect.
2. Contact non-submit `OPEN_RECORD` uses preserved chat focus behavior.
3. Lead non-submit `OPEN_RECORD` remains unchanged from phase 248.
4. Opportunity non-submit `OPEN_RECORD` remains unchanged in this phase.
5. Submit-path no-auto-open behavior for lead/contact/opportunity remains unchanged.
6. DOM-level continuity tests cover contact append order, contact preserved chat focus, and prompt/button-triggered contact action continuity.
