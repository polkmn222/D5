# Testing Runbook

## Default Review Order

1. `docs/agent.md`
2. `docs/codex-working-rules.md`
3. `docs/testing.md`
4. `docs/workflow.md`
5. `docs/spec.md`
6. `docs/testing/README.md`
7. `docs/testing/strategy.md`
8. `docs/testing/known_status.md`

This review order is mandatory before planning or running unit tests.

## Current Practical Commands

- Full unit suite: `PYTHONPATH=development pytest -m unit development/test/unit`
- Full unit suite with failure and skip reasons: `PYTHONPATH=development pytest -m unit development/test/unit -rs -q`
- Focused AI Agent unit suite: `PYTHONPATH=development pytest -m unit development/test/unit/ai_agent/backend -q`
- Non-AI, non-send-message focused suite: run the selected CRM and shared UI files explicitly
- Integration: `TEST_DATABASE_URL=postgresql://... PYTHONPATH=development pytest -m integration development/test/integration`
- Focused AI Agent integration suite: `TEST_DATABASE_URL=postgresql://... PYTHONPATH=development pytest -m integration development/test/integration/ai_agent/backend -q`

## Integration Verification Commands

- Slack dev/test provider verification: run an automated script or test with `MESSAGE_PROVIDER=slack` and confirm the send result is `Sent`.
- SureM carrier verification: run one forced-recipient MMS send only after confirming the protected runtime is configured with the required SureM credentials.
- Provider diagnostics endpoint: `GET /messaging/provider-status`
- Render policy verification: on Render, confirm `/messaging/provider-status` reports `delivery_policy.render_delivery_blocked=true` unless an explicit override is intended.

These are integration checks, not manual testing.

## PostgreSQL Test Setup

- Set `TEST_DATABASE_URL` to an isolated PostgreSQL database before running integration tests.
- Do not point `TEST_DATABASE_URL` at production.
- Integration fixtures are responsible for transaction rollback and test isolation.
- If `TEST_DATABASE_URL` is missing, integration tests must not fall back to SQLite.

## Current Known Status

- The current known full-unit reference result is tracked in `docs/testing/known_status.md`.
- If the suite fails in a way that matches `known_status.md`, record the comparison before changing code or tests.

## Recommended Future Commands After Migration

- Core CRM objects: `pytest development/test/unit/crm`
- Shared UI: `pytest development/test/unit/ui`
- Search: `pytest development/test/unit/search`
- Messaging: `pytest development/test/unit/messaging`
- AI agent: `pytest development/test/unit/ai_agent`

These target folders are still a migration goal. The current canonical commands above remain the source of truth until the folder migration is complete.

## Migration Order

1. Create shared fixture and factory modules.
2. Move shared UI and search tests first.
3. Move core CRM object tests.
4. Move messaging tests.
5. Move AI agent tests.
6. Move or retire legacy phase-named tests.
