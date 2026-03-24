# Phase 36: Complete Removal of Task and Campaign Objects

## Objective
Remove all unused code, database schemas, and documentation related to `Task` and `Campaign` objects.

## Steps
1. Create a backup of `backend`, `frontend`, `db`, and `test` directories.
2. Search for references to `Task` and `Campaign` in the `.gemini/development/` codebase.
3. Remove left-over files: `task_service.py`, `task_router.py`, `task_gemini.py`, `frontend/templates/tasks/`, etc.
4. Remove `Task` model and any `Campaign` model from `db/models.py`.
5. Remove all task and campaign references from UI templates (`sf_form_modal.html`, `detail_view.html` variations, `object_form.html`).
6. Update `metadata.json` and `docs/erd.md`.
7. Execute a python script to drop `tasks` and `campaigns` tables from `crm.db`.
8. Fix unit tests and ensure `pytest` runs cleanly.