# Walkthrough - Phase 75

## What Changed
This phase moved the main web runtime into a canonical `web/` container while preserving compatibility with the previous top-level paths.

## Runtime Structure
- The canonical main runtime now lives under `.gemini/development/web/`.
- Existing `backend/`, `frontend/`, and `app/static/uploads/` paths remain available as compatibility links so legacy imports and assumptions do not break immediately.

## Deployment and Runtime
- Vercel and Render now target `web.backend.app.main:app`.
- Shared frontend assets and upload-backed assets continue to work through explicit static mounts.

## Validation
- Targeted migration-sensitive tests passed.
- Broad regression suite passed with `137 passed`.

## Why This Matters
The web runtime is now easier to reason about as a single containerized subtree, while the migration remains low-risk because compatibility links preserve the old path surface during transition.
