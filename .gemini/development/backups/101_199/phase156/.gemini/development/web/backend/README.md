# Web Backend Guide

## Scope

- This folder owns the main CRM FastAPI application.
- Application entrypoints, routers, services, and shared backend utilities live here.

## Canonical Docs

- Primary rules live in `/.gemini/development/docs/skill.md`.
- Runtime structure lives in `/.gemini/development/docs/architecture.md`.
- Deployment behavior lives in `/.gemini/development/docs/deployment.md`.
- Workflow and backup rules live in `/.gemini/development/docs/workflow.md`.

## Entrypoints

- `app/main.py`: canonical FastAPI app for local runs and Render.
- `app/api/api_router.py`: top-level route composition.
- `app/api/routers/`: object and feature routers.
- `app/services/`: business logic and shared workflows.
- `run_crm.sh`: local startup helper.

## Current Rules

- Keep routers thin and push business logic into services.
- Treat PostgreSQL as the active runtime database.
- Shared template loading is configured through backend code, even when templates live under `web/frontend/` or `web/message/frontend/`.
- The main app mounts the AI sub-app and includes the messaging subsystem.

## Common Gotchas

- Structural changes here often affect routing, template loading, deployment, and tests at the same time.
- Do not duplicate object logic in routers when a service already owns it.
- If a change affects mounts, imports, or entry points, update docs in the same phase.

## Tests

- Core backend unit tests live under `/.gemini/development/test/unit/`.
- Integration tests live under `/.gemini/development/test/integration/`.
