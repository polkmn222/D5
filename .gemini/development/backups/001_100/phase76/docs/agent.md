# D4 Agent Guide

## Purpose

This document is the primary entry point for the active D4 workspace. It absorbs the former high-level `README.md` and retired `GEMINI.md` guidance and points to the current canonical documents for architecture, deployment, workflow, and implementation skills.

## Project Overview

- **Product**: D4 is an AI-assisted automotive CRM built around FastAPI, SQLAlchemy, PostgreSQL, Jinja2 templates, and a mounted AI agent sub-application.
- **Primary runtime**: The canonical main web app lives in `web/backend/`, shared templates and static assets live in `web/frontend/`, shared uploads live in `web/app/static/uploads/`, the database layer lives in `db/`, and the AI assistant lives in `ai_agent/`.
- **Deployment entry points**: Vercel routes traffic through `api/index.py`, while Render starts `web.backend.app.main:app` from `.gemini/development`.
- **AI surface**: The main FastAPI app mounts the AI sub-app at `/ai-agent`, which exposes its own `/api` routes and `/static` assets.

## Current Source of Truth

- `docs/agent.md`: project overview, documentation map, and governance.
- `docs/skill.md`: implementation guidance for backend, frontend, and AI agent work.
- `docs/architecture.md`: active runtime architecture and request flow.
- `docs/deployment.md`: current Vercel and Render deployment model.
- `docs/workflow.md`: phase numbering, artifact storage, and backup policy.
- `docs/erd.md`: current data model reference for active ORM entities.
- `docs/testing/`: canonical testing strategy, runbook, coverage matrix, and migration plan.
- `docs/SESSION_HANDOFF.md`: operational handoff snapshot; useful for current state, but not authoritative when it conflicts with the canonical docs above.

## Active Runtime Structure

- The current top-level folder layout is fixed. Do not move runtime, deployment, test, or documentation roots unless the user explicitly requests a structural migration and the docs are updated in the same phase.
- `api/index.py`: Vercel shim that adds `.gemini/development` to `sys.path` and imports `web.backend.app.main:app`.
- `web/backend/app/main.py`: main FastAPI application, static mount, router registration, and `/ai-agent` mount point.
- `web/backend/app/api/`: route composition and object-specific routers.
- `web/backend/app/services/`: core business logic for CRM objects, messaging, search, dashboards, imports, and attachments.
- `web/frontend/templates/` and `web/frontend/static/`: server-rendered UI and shared front-end assets.
- `.gemini/development/backend` and `.gemini/development/frontend`: compatibility links that point to the canonical `web/` runtime folders.
- `db/database.py` and `db/models.py`: PostgreSQL engine setup, sessions, and ORM models.
- `ai_agent/backend/`: AI chat router, orchestration, providers, and conversation context.
- `test/`: automated tests, manual verification assets, and test-specific notes.

## Technology Baseline

- **Framework**: FastAPI on Python 3.12.
- **Data layer**: SQLAlchemy with PostgreSQL via `psycopg`.
- **Rendering**: Jinja2 templates with vanilla CSS and JavaScript.
- **AI providers**: Cerebras, Groq, Gemini, and OpenAI are supported by the AI agent layer when configured.
- **Testing**: `pytest`, `pytest-asyncio`, and `httpx`.

## Local Development Notes

- Install dependencies from the repository root with `pip install -r requirements.txt`.
- Set `DATABASE_URL` before starting the app. PostgreSQL is mandatory for the active runtime.
- Run the Vercel-style entry from the repository root with `uvicorn api.index:app --reload`.
- Run the app directly from `.gemini/development` with `uvicorn web.backend.app.main:app --reload`.

## Mandatory Rules

### Architecture and Stability

- Keep modules small and responsibility-driven so one feature change does not destabilize unrelated flows.
- Keep routers thin and push business logic into services.
- Treat PostgreSQL as the only supported production database for active application behavior.

### Frontend Organization

- Keep templates organized by object or feature area under `web/frontend/templates/`.
- Keep JavaScript scoped to object or page behavior instead of adding global one-off scripts.
- Preserve the existing server-rendered UI model unless there is a clear architectural reason to change it.

### Field and Navigation Rules

- Avoid exposing raw lookup field labels with trailing `Id` or `ID` in the UI.
- Keep record names clickable in search, related lists, and recent-item surfaces.
- Default new fields to optional unless a real business rule requires otherwise.

### Display and Language Rules

- Render null-like values as blank output in the UI.
- Keep user-facing text, code comments, and documentation in English.
- Preserve the established Salesforce-inspired visual grammar across object pages.

### Error and State Management

- Surface recoverable errors to the UI cleanly instead of failing into raw server traces.
- Keep placeholders and unfinished features behind explicit user-friendly states.
- Preserve existing exception handling patterns in both the main app and AI agent paths.

## Documentation Rules

- Update `docs/agent.md`, `docs/skill.md`, `docs/architecture.md`, and `docs/deployment.md` when runtime behavior changes.
- Do not reintroduce retired `GEMINI.md` guidance as a parallel source of truth.
- Use the next unused phase number across `task/`, `Implementation/`, `Walkthrough/`, and `backups/` before writing artifacts.
- Store backups inside a dedicated `.gemini/development/backups/phaseN/` folder for each phase; do not leave phase backups as loose files at the backups root.
- Create new project-level markdown files under `.gemini/development/docs/` by default.
- Keep root-level markdown files out of the repository root unless the file is a required phase artifact in `task/`, `Implementation/`, or `Walkthrough/`, or a folder-local README that documents a specific subtree.
- Read and follow all active markdown files under `.gemini/development/docs/` before making project changes.

## Delivery Directives

- Save phase tracking files as `task/task_phaseN.md`, `Implementation/Implementation_phaseN.md`, and `Walkthrough/Walkthrough_phaseN.md`.
- When code or active documentation changes, store pre-change backups under `.gemini/development/backups/phaseN/` using phase-specific folders and relative paths.
- When the Antigravity MCP `sequential-thinking` tool is available, use it for structured execution planning; if it is unavailable, do not block work and instead follow the docs-driven workflow automatically.

## Test and Cache Rules

- Use the repository-root `/.pytest_cache` as the only accepted pytest cache location.
- Do not create or preserve duplicate pytest cache directories under `.gemini/`, `.gemini/development/`, or other subfolders.
- Keep `.pytest_cache` ignored by git; it is local execution state and must not be committed.
- Keep the current folder layout intact: `api/`, `task/`, `Implementation/`, `Walkthrough/`, `vercel.json`, `render.yaml`, and `requirements.txt` stay at the repository root, while the active application code remains under `.gemini/development/`.

## Design Principles

1. **Atomic first**: prefer independently testable modules, services, and UI units.
2. **Consistent detail views**: preserve standard tabs, related data surfaces, and responsive field grids.
3. **Traceable delivery**: store phase artifacts and backups for any meaningful documentation or code change.
4. **Documentation follows runtime**: deployment, architecture, and data model docs must reflect the live code path.
