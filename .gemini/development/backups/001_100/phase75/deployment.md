# Deployment

## Overview

The active project supports two deployment paths that both resolve to the same FastAPI application.

## Vercel

- Configuration lives in `vercel.json` at the repository root.
- All routes are sent to `api/index.py`.
- `api/index.py` adds `.gemini/development` to `sys.path` and imports `backend.app.main:app`.
- This path keeps Vercel focused on a thin adapter while the real application remains inside `.gemini/development`.

## Render

- Configuration lives in `render.yaml` at the repository root.
- The web service runs with `rootDir: .gemini/development`.
- Dependencies are installed with `pip install -r ../../requirements.txt`.
- The service starts with `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`.
- The configured health check path is `/docs`.

## Shared Runtime Behavior

- The main application mounts shared static assets at `/static`.
- The AI sub-application is mounted at `/ai-agent`.
- The AI sub-application serves its own assets at `/ai-agent/static` and exposes `/ai-agent/health`.
- Both deployment paths ultimately use the same `backend.app.main:app` process tree.

## Required Environment Variables

### Mandatory

- `DATABASE_URL`: required by `db/database.py`; PostgreSQL is mandatory for the active runtime.

### Messaging

- `MESSAGE_PROVIDER`: `mock` by default, `slack` when webhook-based delivery checks are needed.
- `SLACK_MESSAGE_WEBHOOK_URL`: required only when `MESSAGE_PROVIDER=slack`.
- `APP_BASE_URL`: optional, used to build absolute image URLs for Slack message previews.

### AI Providers

- `CELEBRACE_API_KEY`
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

Not every AI provider key is required at once, but provider-specific features depend on the keys being present.

## Verification Checklist

- Confirm `vercel.json` still routes to `api/index.py`.
- Confirm `render.yaml` still starts `backend.app.main:app` from `.gemini/development`.
- Confirm `docs/architecture.md` matches the current mount points and entry paths.
- Confirm `DATABASE_URL` requirements are documented whenever database setup changes.
