Current handoff state for the D4 repo.

Latest pushed commits
- `cd3b5d8` Messaging provider refactor groundwork
- `ebc414c` Remove runtime deprecation warnings
- `077c3c4` Require PostgreSQL and align unit tests

What changed
- Vercel deployment uses the repo root with `vercel.json` and `api/index.py`.
- Messaging now uses a provider-based architecture with `mock` as the safe default.
- Slack webhook delivery can be enabled for free dev/test verification.
- Template image uploads are stored locally and reused across Send Message and AI Agent flows.

Verified locally
- `PYTHONPATH=.gemini/development pytest --import-mode=importlib .gemini/development/test/unit`
- Result: `112 passed`

Verified online
- App root loads
- `/docs` loads
- `/messaging/ui` loads
- AI Agent flows and Send Message screen load with provider-based messaging configuration.

Likely next production check
- Confirm the deployment environment sets `MESSAGE_PROVIDER` intentionally.
- If using Slack verification, confirm `SLACK_MESSAGE_WEBHOOK_URL` and `APP_BASE_URL` are present.

Required Vercel env vars
- `DATABASE_URL`
- `MESSAGE_PROVIDER`
- `SLACK_MESSAGE_WEBHOOK_URL` (only for Slack-based verification)
- `APP_BASE_URL` (recommended when sending image previews to Slack)

Current uncommitted local changes
- `/.gemini/development/ai_agent/backend/recommendations.py`
- `/.gemini/development/ai_agent/backend/service.py`
- `/.gemini/development/ai_agent/frontend/static/css/ai_agent.css`
- `/.gemini/development/ai_agent/frontend/static/js/ai_agent.js`
- `/.gemini/development/ai_agent/frontend/templates/ai_agent.html`
- `/.gemini/development/backend/app/api/routers/dashboard_router.py`
- `/.gemini/development/frontend/templates/dashboard/dashboard_ai_recommend_fragment.html`
- `/.gemini/development/test/unit/test_ai_recommend_logic.py`

Notes
- Render auto-deploy was turned off to stop repeated failure emails.
- Vercel auth protection was turned off earlier so public checks work.
