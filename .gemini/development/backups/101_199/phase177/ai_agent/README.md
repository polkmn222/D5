# AI Agent Guide

## Scope

- This folder owns the mounted AI assistant runtime.
- The AI Agent is separated into an `llm` (reasoning) pillar and a `ui` (presentation) pillar.
- `llm/backend/`: Core intent classification and conversation context.
- `ui/backend/`: Orchestration, API routing, and DB operations.
- `ui/frontend/`: Static JS/CSS and UI templates.

## Canonical Docs

- Primary rules live in `/.gemini/development/docs/skill.md`.
- Runtime structure lives in `/.gemini/development/docs/architecture.md`.
- AI runtime notes live in `/.gemini/development/docs/agent.md`.
- Testing rules live in `/.gemini/development/docs/testing/`.

## Entrypoints

- `llm/backend/intent_preclassifier.py`: Rule-based intent detection.
- `llm/backend/intent_reasoner.py`: LLM-based complex intent detection.
- `llm/backend/ai_service.py`: LLM provider fanout and shared AI utilities.
- `ui/backend/main.py`: Mounted sub-application.
- `ui/backend/router.py`: `/api/chat`, `/api/reset`, and `/health`.
- `ui/backend/service.py`: Orchestration, record actions, and LLM provider fanout.
- `ui/frontend/static/`: Agent JS and CSS.
- `ui/frontend/templates/`: AI agent UI fragments and templates.

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
