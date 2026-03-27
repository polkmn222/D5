Phase 258 Walkthrough

Behavior
- `Manage brand <id>` now returns `OPEN_RECORD` with a brand chat card.
- Brand selection/table `Open` now routes through chat first.
- Brand non-submit `OPEN_RECORD` now keeps the newest chat result visible before workspace open.
- Brand chat-card `Open Record` now uses explicit display-first routing.

Verification
- Covered by the focused non-DB unit/DOM suite rerun that passed after the brand changes were added.

Notes
- This kept the `brand/model` group progression narrow by stopping at open/view behavior only.
