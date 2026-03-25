# Phase 125 Task

## Context

AI Recommend should stamp opportunity updates with `AI Recommend` metadata and avoid re-running the full refresh more than once per day. AI Agent `Open`, `Edit`, and `Send Message` should all stay fully inside the chat workspace instead of navigating away.

## Goals

- Persist `updated_by = AI Recommend` on opportunity temperature refreshes and skip repeat same-day refreshes.
- Make AI Agent `Open`, `Edit`, and `Send Message` all render inside the in-chat workspace.
- Keep loading states and name-based UX intact.
