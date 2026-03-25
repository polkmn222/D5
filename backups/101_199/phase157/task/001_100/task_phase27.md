# Task: Phase 27 - Database Consolidation & Cleanup

## Objective
Organize all SQLite database files within the `.gemini/development/` directory. Consolidate the active `crm.db` into the development root, move all test-related `.db` files into a dedicated `test_runs` directory, and remove redundant database copies to ensure a single source of truth.

## Sub-tasks
1. Create `.gemini/development/db/test_runs/` for temporary test databases.
2. Move all `test_*.db`, `test.db`, and `test_refactor.db` files into `db/test_runs/`.
3. Consolidate `crm.db` at the root of `.gemini/development/`.
4. Create a relative symlink `.gemini/development/db/crm.db -> ../crm.db` to maintain compatibility with backend services that reference the database relative to the `db/` folder.
5. Delete redundant `crm.db` files found in `vercel_render/`, `tmp_system/`, and `backend/app/` directories.
6. Verify server connectivity after the database reorganization.

## Completion Criteria
- Only one active `crm.db` exists in the `development/` root.
- All test databases are moved to `db/test_runs/`.
- `run_crm.sh` successfully launches the server using the consolidated database.
- Phase 27 documentation is generated.