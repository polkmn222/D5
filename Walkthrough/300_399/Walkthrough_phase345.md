# Phase 345 Walkthrough

## What Changed

- `MessagingService.send_message()` now fails fast on Render unless `ALLOW_MESSAGE_SEND_ON_RENDER=true` is explicitly set.
- `relay-dispatch` now returns a blocked response on Render under the same policy.
- `/messaging/provider-status` now exposes `delivery_policy.render_delivery_blocked`.
- `/messaging/demo-availability` reports `render_delivery_blocked` when the runtime is on Render.

## Verification

- Focused unit tests were run for provider status, relay dispatch, demo availability, send limits, relay provider behavior, template submission continuity, and the relay-only app surface.
