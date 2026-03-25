# Session Handoff

This file is an operational handoff snapshot for the current local and deployment state.

If any statement here conflicts with `docs/agent.md`, `docs/deployment.md`, or `docs/workflow.md`, treat those canonical documents as the source of truth.

This handoff file records temporary operating context and should not replace the standing rules in `docs/agent.md`, `docs/workflow.md`, `docs/skill.md`, or the rest of the active `docs/` set.

## Latest Pushed Commits
- `cd3b5d8` Messaging provider refactor groundwork
- `ebc414c` Remove runtime deprecation warnings
- `077c3c4` Require PostgreSQL and align unit tests

## What Changed
- Vercel deployment uses the repo root with `vercel.json` and `api/index.py`.
- The canonical main web runtime now lives under `.gemini/development/web/`.
- Messaging-specific backend/services/templates now live under `.gemini/development/web/message/`.
- Messaging now uses a provider-based architecture with `mock` as the safe default.
- Slack webhook delivery can be enabled for free dev/test verification.
- Template image uploads default to local storage, and Cloudinary can be enabled for public MMS image hosting across Send Message and AI Agent flows.

## Verified Locally
- `PYTHONPATH=.gemini/development pytest --import-mode=importlib .gemini/development/test/unit`
- Result: `112 passed`

## Verified Online
- App root loads
- `/docs` loads
- `/messaging/ui` loads
- AI Agent flows and Send Message screen load with provider-based messaging configuration.

## Likely Next Production Check
- Confirm the deployment environment sets `MESSAGE_PROVIDER` intentionally.
- If using Slack verification, confirm `SLACK_MESSAGE_WEBHOOK_URL` and `APP_BASE_URL` are present.

## Required Vercel Env Vars
- `DATABASE_URL`
- `MESSAGE_PROVIDER`
- `SLACK_MESSAGE_WEBHOOK_URL` (only for Slack-based verification)
- `APP_BASE_URL` (recommended only when local uploads need a public hostname or tunnel)
- `CLOUDINARY_CLOUD_NAME` plus either signed credentials or an unsigned upload preset for public MMS image hosting

## Current Uncommitted Local Changes
- `/.gemini/development/ai_agent/backend/recommendations.py`
- `/.gemini/development/ai_agent/backend/service.py`
- `/.gemini/development/ai_agent/frontend/static/css/ai_agent.css`
- `/.gemini/development/ai_agent/frontend/static/js/ai_agent.js`
- `/.gemini/development/ai_agent/frontend/templates/ai_agent.html`
- `/.gemini/development/web/backend/app/api/routers/dashboard_router.py`
- `/.gemini/development/web/frontend/templates/dashboard/dashboard_ai_recommend_fragment.html`
- `/.gemini/development/test/unit/test_ai_recommend_logic.py`

## Notes
- Render auto-deploy was turned off to stop repeated failure emails.
- Vercel auth protection was turned off earlier so public checks work.
