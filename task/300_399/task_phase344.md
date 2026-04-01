# Phase 344 Task

## Request

Proceed with the safer deployment option that separates carrier delivery onto a dedicated fixed-IP relay runtime.

## Scope

- Add a relay-only runtime entry for protected message handoff.
- Keep the existing full app runtime intact.
- Add focused unit tests for the relay-only runtime surface.
- Update deployment documentation for the separated relay topology.

## Constraints

- Do not expand scope beyond the dedicated relay deployment path.
- Use unit tests only.
- Do not use manual testing.
- Do not reintroduce Solapi.

## Success Criteria

- The repository contains a dedicated relay-only FastAPI entry point.
- The relay-only runtime exposes only the minimal relay and diagnostics endpoints.
- Focused messaging unit tests pass.
- Deployment docs describe the fixed-IP relay topology and required environment variables.
