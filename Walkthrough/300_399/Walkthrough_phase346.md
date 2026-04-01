# Phase 346 Walkthrough

## What Changed

- The web Send Message screen now keeps the availability banner and changes the primary button label to `Contact Administrator` when messaging is blocked.
- AI Agent now fetches messaging availability on load and applies that state to:
  - the quick Send Message card
  - the selection-bar Send Message button
  - chat-card Send Message actions
  - direct Send Message quick-command entry
- When blocked, AI Agent shows the administrator-contact message instead of opening the send flow.

## Verification

- Focused unit tests were run for the Send Message template, AI Agent continuity DOM behavior, and the existing messaging provider and availability behavior.
