# D4 Implementation Skills

## Purpose

This document describes the practical implementation guidance for the three active application surfaces: `web/backend`, `web/frontend`, and `ai_agent`.

## Backend

### Scope

- The main FastAPI application lives in `web/backend/app/`.
- Request composition begins in `web/backend/app/main.py` and `web/backend/app/api/api_router.py`.
- Business logic lives in `web/backend/app/services/`.
- Shared enums, template helpers, toggles, and utility code live under `web/backend/app/core/` and `web/backend/app/utils/`.

### Core Expectations

- Keep routers focused on request validation, dependency wiring, and response formatting.
- Keep object behavior, workflow logic, and cross-object coordination inside services.
- Reuse `db.database.get_db` for database sessions and keep PostgreSQL assumptions compatible with the active runtime.
- Preserve shared patterns for error handling, redirects, and JSON error responses.
- Update architecture and deployment docs whenever entry points, mounts, or environment requirements change.

### High-Value Areas

- CRM object flows: leads, contacts, opportunities, assets, products, vehicle specifications.
- Messaging flows: templates, sends, attachments, provider-based delivery, and free dev/test channel validation.
- Use `mock` as the safest local default and `slack` as the preferred free dev/test verification channel before any production-grade delivery provider is introduced.
- Search and dashboard aggregation.
- Import and attachment workflows.

## Frontend

### Scope

- Shared CRM templates live in `web/frontend/templates/`.
- Shared CSS and JavaScript live in `web/frontend/static/`.
- Template loading is configured centrally through `web/backend/app/core/templates.py`.

### Core Expectations

- Treat the UI as server-rendered first, with JavaScript enhancing interactions rather than replacing page structure.
- Preserve object-specific template organization and keep reusable partials consistent.
- Follow `docs/ui_standards.md` for detail layouts, tabs, inline editing, bulk actions, and blank-value rendering.
- Keep style and interaction changes consistent with the existing Salesforce-inspired product language.
- Verify both desktop and mobile behavior when changing page structure or interactive controls.

### High-Value Areas

- Object list and detail views.
- Shared layout, navigation, and template filters.
- Messaging screens and send flows.
- Front-end hooks that coordinate with API responses and toast-style feedback.

## AI Agent

### Scope

- The AI sub-application lives in `ai_agent/backend/` and `ai_agent/frontend/`.
- `ai_agent/backend/main.py` defines the mounted sub-app.
- `ai_agent/backend/router.py` exposes `/api/chat`, `/api/reset`, and `/health`.
- `ai_agent/backend/service.py` orchestrates provider fanout, intent handling, record lookup, and action execution.

### Core Expectations

- Keep the AI agent compatible with the main app mount path at `/ai-agent`.
- Reuse main-app services and shared database sessions instead of duplicating CRM business rules.
- Preserve conversation context, selection state, and confirmation flows for destructive actions.
- Document provider behavior when adding or removing supported models or API keys.
- Keep response contracts stable for the AI front-end experience.

### High-Value Areas

- Intent classification and reasoning.
- Record creation, management, deletion confirmation, and messaging flows.
- Provider fanout across Cerebras, Groq, Gemini, and OpenAI.
- Conversation memory, pagination, and contextual follow-up handling.

## Cross-Cutting Delivery Rules

- Update docs when runtime behavior changes.
- Use the next unused phase number before creating `task`, `Implementation`, `Walkthrough`, or `backups` artifacts.
- Store pre-change copies of touched files under `.gemini/development/backups/phaseN/`.
- Run focused verification for the surfaces you touch and record it in the phase walkthrough.
