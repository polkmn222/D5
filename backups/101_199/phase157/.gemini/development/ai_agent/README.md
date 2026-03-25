# AI Agent Guide

## Scope

- This folder owns the mounted AI assistant runtime.
- Backend code lives in `backend/`.
- Frontend assets and templates live in `frontend/`.

## Canonical Docs

- Primary rules live in `/.gemini/development/docs/skill.md`.
- Runtime structure lives in `/.gemini/development/docs/architecture.md`.
- AI runtime notes live in `/.gemini/development/docs/agent.md`.
- Testing rules live in `/.gemini/development/docs/testing/`.

## Entrypoints

- `backend/main.py`: mounted sub-application.
- `backend/router.py`: `/api/chat`, `/api/reset`, and `/health`.
- `backend/service.py`: orchestration, intent handling, record actions, and provider fanout.
- `frontend/static/`: agent JS and CSS.
- `frontend/templates/`: AI agent UI fragments and templates.

## Current Rules

- The main app mounts the sub-app at `/ai-agent`.
- The user-facing dashboard entry is the lazy-loaded `/ai-agent-panel` fragment.
- Runtime manual validation should use `/ai-agent-panel`, `/ai-agent/api/chat`, and `/ai-agent/api/reset`.
- Preserve conversation context, recent-record context, selection state, and destructive-action confirmations.

## Common Gotchas

- Do not confuse direct service calls with mounted runtime behavior.
- `test/manual/ai_agent/verify_responses.py` is a service-level debug harness, not a full runtime manual test.
- Keep docs, tests, and pre-classifier behavior aligned before changing `just created` or recent-record logic.

## Tests

- AI backend tests live under `/.gemini/development/test/unit/ai_agent/backend/`.
- AI frontend/runtime tests live under `/.gemini/development/test/unit/ai_agent/frontend/`.
- Manual AI assets live under `/.gemini/development/test/manual/ai_agent/`.
