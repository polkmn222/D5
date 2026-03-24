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
5. Run `python .gemini/development/test/manual/smoke/smoke_checklist.py` for an interactive smoke checklist, or add `--print-only` to review without recording results.
6. Run `python .gemini/development/test/manual/regression/regression_checklist.py` for an interactive regression checklist, or add `--print-only` to review without recording results.
7. Run AI-agent or messaging manual checks only if those domains are in scope.
8. Let the helper scripts save markdown reports under `test/manual/evidence/`, and store any extra screenshots or notes there without committing them.

## Messaging-Specific Notes

- Messaging UI templates resolve from `web/message/frontend/templates/`, not from `web/frontend/templates/`.
- During manual verification, treat the current `messages/detail_view.html` surface as intentionally read-only.
- Treat `message_templates/detail_view.html` as the editable messaging detail surface.

## Report Output

- The helper scripts generate markdown reports with summary counts, failure highlights, area summaries, and per-item notes.
- When failures exist, the helper scripts also generate a failed-item rerun checklist as a separate markdown file.
- Use `--report-name <name>` to customize the report filename prefix.
- Use `--no-save` when you want to run interactively without writing evidence files.

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
