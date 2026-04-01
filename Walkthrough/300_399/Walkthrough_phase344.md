# Phase 344 Walkthrough

## What Changed

- The repository now supports a dedicated relay-only runtime that serves only:
  - `/health`
  - `/messaging/provider-status`
  - `/messaging/demo-availability`
  - `/messaging/demo-relay-health`
  - `/messaging/relay-dispatch`
- Shared relay diagnostics and dispatch behavior were moved into a common helper module so the full app and the relay-only runtime use the same logic.
- A separate `render.relay.yaml` deployment template was added for fixed-IP relay hosting.

## Why

- The SureM runtime path may reject requests from unapproved or foreign egress IPs.
- Separating the relay onto a protected host lets the full app keep using `MESSAGE_PROVIDER=relay` while the fixed-IP host performs the final carrier handoff.
- The relay-only runtime avoids mounting the UI and AI surfaces, which reduces exposure and unnecessary dependencies on the protected host.

## Verification

- Focused unit tests were run for relay provider behavior, relay dispatch, relay diagnostics, message template submission continuity, and the new relay-only app surface.
- The relay-only app test confirms the runtime exposes a health endpoint, forwards relay dispatch correctly, and does not expose `/messaging/ui`.
