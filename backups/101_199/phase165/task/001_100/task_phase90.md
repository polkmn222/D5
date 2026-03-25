# Phase 90 Task

## Context

The recommended long-term fix for MMS preview reliability is public object storage instead of local-only uploads. Slack MMS verification now works through a temporary tunnel, but the app still needs first-class support for public image hosting.

## Goals

- Add Cloudinary-backed image upload support for messaging template images.
- Preserve local upload fallback when Cloudinary is not configured.
- Reuse the same storage path for Send Message template uploads and legacy template upload routes.
- Document the new environment variables and test the routing behavior.

## Constraints

- Follow the active docs under `.gemini/development/docs/`.
- Use phase `90` consistently for task, implementation, walkthrough, and backups.
- Back up every touched existing file under `.gemini/development/backups/phase90/` before editing.
