# Manual Testing Runbook

## Review Order

1. `docs/agent.md`
2. `docs/workflow.md`
3. `docs/spec.md`
4. `docs/testing/README.md`
5. `docs/testing/manual_strategy.md`
6. `docs/testing/manual_checklist.md`

## Recommended Execution Order

1. Confirm `TEST_DATABASE_URL` points to a dedicated PostgreSQL test database.
2. Optionally set `D4_RESET_MANUAL_TEST_DB=1` if a clean reset is required.
3. Run any needed setup helper from `test/manual/data_setup/`.
4. Start the app with `./run_crm.sh`.
5. Execute smoke checks from `manual_checklist.md`.
6. Execute the relevant CRM regression sections.
7. Run AI-agent or messaging manual checks only if those domains are in scope.
8. Store local screenshots or notes under `test/manual/evidence/` without committing them.

## Script Classification

- `test/manual/data_setup/generate_rich_data.py`: reusable setup helper
- `test/manual/ai_agent/verify_responses.py`: active AI-agent manual check
- `test/manual/ai_agent/legacy/*`: historical AI-agent scripts retained for reference
- `test/manual/legacy/*`: stale scripts with outdated imports, routes, or assumptions

## Failure Recording

When a manual check fails, record:

- page or route
- object type
- exact steps
- expected result
- actual result
- whether the issue reproduces after restart or DB reset
