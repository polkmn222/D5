# Project Architecture

## Overview

D4 is a modular FastAPI application with a mounted AI sub-application, a shared PostgreSQL-backed ORM layer, and a server-rendered Jinja2 frontend.

## High-Level Architecture Diagram

```mermaid
graph TD
    User((Browser)) --> Edge[Platform Entry]
    Edge --> MainApp[FastAPI Main App]
    MainApp --> Routers[CRM Routers]
    MainApp --> Templates[Jinja2 Templates]
    MainApp --> Static[/static]
    MainApp --> AIAgent[/ai-agent Sub-app]
    Routers --> Services[Backend Services]
    AIAgent --> AgentRouter[AI Agent Router]
    AgentRouter --> AgentService[AI Agent Service]
    AgentService --> Services
    Services --> ORM[SQLAlchemy Models and Sessions]
    ORM --> Postgres[(PostgreSQL)]
    Templates --> SharedUI[frontend/templates + ai_agent templates]
```

## Entry Points

- `api/index.py`: repository-root adapter used by Vercel. It inserts `.gemini/development` into `sys.path` and imports `backend.app.main:app`.
- `backend/app/main.py`: canonical FastAPI application for local runs and Render.
- `ai_agent/backend/main.py`: sub-application mounted by the main app at `/ai-agent`.

## Runtime Layers

### 1. Delivery Layer

- Vercel forwards all routes to `api/index.py`.
- Render starts `uvicorn backend.app.main:app` from `.gemini/development`.
- The main app serves `/static` for the shared frontend and mounts `/ai-agent` for the AI assistant.

### 2. Presentation Layer

- The CRM UI is rendered through Jinja2 templates under `frontend/templates/`.
- Shared template configuration lives in `backend/app/core/templates.py`.
- Template search paths include both the main frontend templates and AI agent templates.
- Vanilla CSS and JavaScript under `frontend/static/` provide page behavior and UI polish.

### 3. Routing Layer

- Route composition lives in `backend/app/api/api_router.py`.
- Main router groups include dashboard, forms, leads, contacts, opportunities, assets, products, vehicle specifications, messages, templates, bulk actions, utility routes, and messaging flows.
- The AI agent exposes dedicated routes through `ai_agent/backend/router.py`.

### 4. Service Layer

- CRM business logic lives in `backend/app/services/`.
- Shared service patterns handle CRUD, search, dashboards, messaging, imports, attachments, and provider integrations.
- The AI agent service orchestrates intent resolution, record operations, provider fanout, and follow-up context by reusing the shared backend services where possible.

### 5. Data Layer

- `db/database.py` loads environment variables, normalizes `DATABASE_URL`, and builds the SQLAlchemy engine.
- PostgreSQL is mandatory for the active runtime.
- `db/models.py` defines the ORM entities and shared audit fields.

## Core Entities

- `Contact`
- `Lead`
- `Opportunity`
- `Asset`
- `Product`
- `VehicleSpecification`
- `Model`
- `MessageSend`
- `MessageTemplate`
- `Attachment`
- `ServiceToken`

## Request Flow

1. A request enters through Vercel or Render.
2. `backend.app.main:app` handles middleware, exception handling, static mounting, router inclusion, and AI agent mounting.
3. A CRM route delegates business logic to the appropriate backend service.
4. Services operate on SQLAlchemy models and persist through PostgreSQL.
5. The response returns either HTML, redirect responses, or JSON.
6. AI requests under `/ai-agent` flow through the AI router and service, which can call shared services and database access paths.

## Architectural Principles

- Keep routers thin and services explicit.
- Keep the AI agent as a mounted sub-app, not a parallel deployment tree.
- Keep templates server-rendered first, with JavaScript as enhancement.
- Keep documentation aligned with the active entry points and deployment model.
