# System Blueprint

## Canonical References

- Read `agent.md` first for the current workspace guide.
- Read `architecture.md` for the live runtime model.
- Read `deployment.md` for Vercel and Render behavior.
- Read `skill.md` for implementation guidance by application surface.

## Technical Stack

- **Framework**: FastAPI on Python 3.12.
- **ORM**: SQLAlchemy 2.x.
- **Database**: PostgreSQL through `psycopg`.
- **Frontend**: Jinja2 templates with vanilla CSS and JavaScript.
- **AI Integration**: Cerebras, Groq, Gemini, and OpenAI support in the AI agent layer.
- **Testing**: Pytest, pytest-asyncio, and httpx.

## Architecture Snapshot

1. `api/index.py` provides the Vercel import bridge.
2. `web/backend/app/main.py` is the main web application.
3. `web/backend/app/api/` defines CRM routes and route composition.
4. `web/backend/app/services/` contains business logic.
5. `db/` contains engine configuration and ORM models.
6. `web/frontend/` contains shared templates and static assets.
7. `ai_agent/` contains the mounted AI assistant sub-application.

## Implementation Priorities

- Keep runtime docs synchronized with entry-point and deployment changes.
- Preserve object-specific UI consistency in list and detail pages.
- Reuse service-layer logic across both the main app and the AI agent.
- Keep phase artifacts and backups for meaningful changes.
