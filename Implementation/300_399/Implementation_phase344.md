# Phase 344 Implementation

## Summary

- Added a dedicated relay-only FastAPI app at `web.message.backend.relay_app`.
- Extracted shared relay diagnostics and dispatch logic into `web.message.backend.relay_runtime`.
- Added `render.relay.yaml` so a protected fixed-IP host can run the relay-only runtime separately from the full app.
- Updated deployment and agent docs to describe the dedicated relay topology and its reduced environment requirements.
- Added focused unit coverage for the relay-only app surface.
