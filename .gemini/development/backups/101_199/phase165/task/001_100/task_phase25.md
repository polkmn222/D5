# Task: Phase 25 - Restructure and Path Fixes

## Objective
Reorganize the project structure based on manual folder moves. The core application logic (`backend`, `frontend`, `ai_agent`, `db`, `test`) has been consolidated inside the `.gemini/development/` directory. Fix script paths (`run_crm.sh`), update Python imports across the test suite, and run unit tests.

## Sub-tasks
1. Consolidate `Development`, `db`, and `test` into `.gemini/development/`.
2. Update `run_crm.sh` to correctly determine `PROJECT_ROOT` and set `PYTHONPATH`.
3. Fix all broken imports (e.g., `backend.app.database` -> `db.database`, `backend.app.models` -> `db.models`) in the test suite.
4. Update `AiAgentService` imports and references in AI tests.
5. Run the unit test suite (`pytest`) to ensure the application imports are healthy.

## Completion Criteria
- `./run_crm.sh` starts the backend server correctly.
- Test files can be collected and executed via `pytest` without major `ImportError` or `ModuleNotFoundError`.
- Phase 25 documentation is generated.