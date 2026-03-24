# Deployment

## Overview

The active project supports two deployment paths that both resolve to the same FastAPI application.

## Vercel

- Configuration lives in `vercel.json` at the repository root.
- All routes are sent to `api/index.py`.
- `api/index.py` adds `.gemini/development` to `sys.path` and imports `web.backend.app.main:app`.
- This path keeps Vercel focused on a thin adapter while the real application remains inside `.gemini/development`.

## Render

- Configuration lives in `render.yaml` at the repository root.
- The web service runs with `rootDir: .gemini/development`.
- Dependencies are installed with `pip install -r ../../requirements.txt`.
- The service starts with `uvicorn web.backend.app.main:app --host 0.0.0.0 --port $PORT`.
- The configured health check path is `/docs`.

## Shared Runtime Behavior

- The main application mounts shared static assets at `/static`.
- Messaging-specific templates are loaded from `web/message/frontend/templates/` through the shared Jinja configuration.
- The AI sub-application is mounted at `/ai-agent`.
- The AI sub-application serves its own assets at `/ai-agent/static` and exposes `/ai-agent/health`.
- Both deployment paths ultimately use the same `web.backend.app.main:app` process tree.

## Required Environment Variables

### Mandatory

- `DATABASE_URL`: required by `db/database.py`; PostgreSQL is mandatory for the active runtime.

### Messaging

- `MESSAGE_PROVIDER`: `mock` by default, `slack` for dev/test notifications, `solapi` for real carrier delivery.
- `SLACK_MESSAGE_WEBHOOK_URL`: required only when `MESSAGE_PROVIDER=slack`.
- `APP_BASE_URL`: optional fallback used to build absolute image URLs when uploads remain local.
- `CLOUDINARY_CLOUD_NAME`: enables Cloudinary-backed public MMS image hosting when set.
- `CLOUDINARY_API_KEY` and `CLOUDINARY_API_SECRET`: recommended signed Cloudinary upload/delete credentials.
- `CLOUDINARY_UNSIGNED_UPLOAD_PRESET`: optional upload-only alternative when signed credentials are not available.
- `SOLAPI_API_KEY` and `SOLAPI_API_SECRET`: required when `MESSAGE_PROVIDER=solapi`.
- `SOLAPI_SENDER_NUMBER`: registered Solapi sender number used for SMS/LMS/MMS dispatch.
- `SOLAPI_ALLOWED_IP`: optional operator note for the allowlisted outbound IP used in the Solapi console.
- `SOLAPI_FORCE_TO_NUMBER`: optional safety override that forces every Solapi send to a single test recipient.

#### Slack Dev/Test Setup

1. Create a Slack Incoming Webhook for a private dev/test channel.
2. Set `MESSAGE_PROVIDER=slack`.
3. Set `SLACK_MESSAGE_WEBHOOK_URL` to the webhook URL.
4. Prefer Cloudinary env vars for public MMS image URLs.
5. If using local uploads instead, set `APP_BASE_URL` to a public hostname or tunnel URL.
6. Run the normal Send Message flow; SMS/LMS/MMS are delivered as Slack-formatted dev/test notifications instead of carrier messages.

#### Solapi Carrier Setup

1. Create Solapi API credentials and allowlist the runtime IP in the Solapi console if the account is IP-restricted.
2. Register and activate at least one sender number in Solapi.
3. Set `MESSAGE_PROVIDER=solapi`.
4. Set `SOLAPI_API_KEY`, `SOLAPI_API_SECRET`, and `SOLAPI_SENDER_NUMBER`.
5. Keep MMS images at 200KB or smaller; Solapi rejects larger MMS uploads.
6. Run the Send Message flow; SMS/LMS go straight to carrier delivery and MMS images are uploaded to Solapi storage before send.

### AI Providers

- `CELEBRACE_API_KEY`
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

Not every AI provider key is required at once, but provider-specific features depend on the keys being present.

## Verification Checklist

- Confirm `vercel.json` still routes to `api/index.py`.
- Confirm `render.yaml` still starts `web.backend.app.main:app` from `.gemini/development`.
- Confirm `docs/architecture.md` matches the current mount points and entry paths.
- Confirm `DATABASE_URL` requirements are documented whenever database setup changes.
