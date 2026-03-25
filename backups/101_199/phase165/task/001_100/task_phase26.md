# Task: Phase 26 - Project Folder Consolidation & Straightening

## Objective
Consolidate all operational and application-related files into the `.gemini/development/` directory. Move `vercel_render`, `backups`, `docs`, `static`, `task`, `tmp`, and database/log files. Separate the "application brain" (`skills/`) from the "application body" (`development/`).

## Sub-tasks
1. Move `.gemini/vercel_render` to `.gemini/development/vercel_render`.
2. Move `.gemini/backups`, `.gemini/static`, `.gemini/task`, `.gemini/tmp` into consolidated subfolders within `.gemini/development/`.
3. Move `.gemini/skills/docs` to `.gemini/development/docs`.
4. Move `.gemini/.env`, `crm.db`, `crm.log`, and all test databases into `.gemini/development/`.
5. Update root `run_crm.sh` symlink to point to `.gemini/development/backend/run_crm.sh`.
6. Ensure no empty or redundant folders remain at the `.gemini/` root level.

## Completion Criteria
- Root `run_crm.sh` executes correctly and starts the server.
- `.gemini/` only contains `development/` and `skills/`.
- Phase 26 documentation is generated.