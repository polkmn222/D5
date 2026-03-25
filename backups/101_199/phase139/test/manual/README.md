# Manual Test Assets

This folder contains active and legacy manual-testing assets.

- `smoke/` holds quick pre-release checks.
- `regression/` holds broader scenario-oriented checks.
- `data_setup/` holds reusable data preparation helpers.
- `ai_agent/` holds active AI-agent manual scripts.
- `legacy/` holds outdated or historical scripts.
- `evidence/` is for local screenshots or notes and is not committed.

Practical helpers:

- `python .gemini/development/test/manual/smoke/smoke_checklist.py`
- `python .gemini/development/test/manual/regression/regression_checklist.py`

Both helpers support:

- `--print-only` to review the checklist without interactive prompts
- `--no-save` to skip writing a report
- `--report-name <name>` to customize the markdown evidence filename prefix
- automatic failed-item rerun checklist generation when any item is marked `fail`

Read `.gemini/development/docs/testing/manual_strategy.md` and `.gemini/development/docs/testing/manual_runbook.md` before using these assets.
