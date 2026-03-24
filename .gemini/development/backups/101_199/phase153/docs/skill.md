# D4 Implementation Skills

## Purpose

This document describes the practical implementation guidance for the four active application surfaces: `web/backend`, `web/frontend`, `web/message`, and `ai_agent`.

## Documentation Priority

- Use `docs/*.md` as the primary D4 implementation rules.
- Use `docs/testing/*.md` as the primary D4 testing rules.
- Use `docs/skills/agency-agents/D4_USAGE.md` when consulting imported skill libraries.
- Treat imported `docs/skills/agency-agents/**` files as supplemental references only.

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
- Split-template ownership: core CRM pages in `web/frontend/templates/`, messaging pages in `web/message/frontend/templates/`.
- Object-specific exceptions such as `web/message/frontend/templates/messages/detail_view.html`, which uses object-level edit actions instead of shared inline-pencil editing.

## Message

### Scope

- Messaging-specific backend logic lives under `web/message/backend/`.
- Messaging-specific templates live under `web/message/frontend/templates/`.
- The main app includes the message subsystem through `web/backend/app/api/api_router.py` and shared template loading.

### Core Expectations

- Keep message sending, template management, provider dispatch, and send UI behavior isolated from general CRM modules where possible.
- Reuse shared CRM services only where messaging needs core objects like contacts, opportunities, and attachments.
- Keep provider-based delivery flows (`mock`, `slack`) documented and test-safe.
- Preserve the current SMS rule that subjects are omitted for SMS templates and SMS sends.
- Keep direct-call tests aligned with the active route signatures in both `web/message/backend/router.py` and `web/message/backend/routers/`.

### High-Value Areas

- Send Message UI and duplicate-recipient review.
- Template CRUD, preview, and MMS image handling.
- Provider abstraction and dev/test delivery workflows.

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
- Prefer an embedded lead create form for `create lead` so the user can fill the actual CRM fields inside the AI conversation.
- Prefer chat-embedded pasted cards for the lead open and edit path when the goal is to keep the user inside the AI conversation rather than bouncing them into a separate workspace.
- After embedded lead-form saves, return a clear success or failure message in chat and show the open-style lead card again.
- When a user explicitly edits the active lead, prefer opening the real lead edit form inline in chat instead of replying with a generic guidance message.
- Preserve contextual lead edit follow-ups so short field-only replies can update the active lead in chat without restating the record ID.
- Preserve recent-created lead recall from conversation memory for both English and Korean phrasings such as `show the lead I just created` and `방금 생성한 lead 보여줘`.
- Keep lead open cards actionable with direct in-chat `Edit` and `Delete` affordances, and prefer user-meaningful lead details in delete success copy.
- Preserve the normalized selection payload shape, which may include `labels` even when the incoming selection payload omitted them.
- Align recent-record and `just created` behavior across docs, pre-classification rules, and tests before changing either the AI flow or the assertions.

### High-Value Areas

- Intent classification and reasoning.
- Record creation, management, deletion confirmation, and messaging flows.
- Provider fanout across Cerebras, Groq, Gemini, and OpenAI.
- Conversation memory, pagination, and contextual follow-up handling.

## Cross-Cutting Delivery Rules

- Update docs when runtime behavior changes.
- Use the next unused phase number before creating `task`, `Implementation`, `Walkthrough`, or `backups` artifacts.
- Store pre-change copies of touched files under the matching grouped backup path such as `.gemini/development/backups/101_199/phaseN/`.
- Run focused verification for the surfaces you touch and record it in the phase walkthrough.
- Prefer adding D4-specific wrapper or usage docs beside imported skill libraries instead of editing generated third-party content directly.
