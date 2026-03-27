## Phase 248 Task Record

### Scope

- Lead-only non-submit `OPEN_RECORD` continuity and scroll polish.
- Frontend-only first.
- Narrow scope only.

### Approved Direction

- Keep the newest lead result visible in the latest chat area.
- Do not let the workspace steal visible focus for the lead non-submit `OPEN_RECORD` path.
- Keep workspace compatibility if needed.
- Preserve the downward chat flow.
- Do not broaden this to contact or opportunity.
- Do not change submit-path behavior completed in earlier phases.

### Target Flows

- Lead prompt-driven open/manage flows that resolve to `OPEN_RECORD`.
- Lead card `Open Record` actions that round-trip through chat.
- Lead selection/table `Open` actions that already route through chat paste.
- `open the lead I just created` / `show the lead I just created` style flows when they resolve to lead `OPEN_RECORD`.

### Constraints

- No broad multi-object continuity rewrite.
- No backend contract change unless a blocker is found and reported first.
- No wording-only cleanup without real continuity improvement.
- No workspace-model redesign.
- Unit tests plus narrow DOM-level UI tests only.
- No browser automation.
- Manual testing is forbidden.

### Required Tests

1. Lead non-submit `OPEN_RECORD` appends the chat result/card in the latest chat area.
2. Lead non-submit `OPEN_RECORD` preserves chat focus instead of letting workspace steal visible focus.
3. Prompt/button-triggered lead actions scroll the newest active chat area into view.
4. Lead selection/open flow still routes through chat paste behavior.
5. Contact and opportunity behavior remain unchanged in this phase.
6. Submit-path no-auto-open behavior from earlier phases remains unchanged.
