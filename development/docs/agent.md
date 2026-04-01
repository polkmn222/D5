# Agent Guide

## Purpose

This document is the primary entry point for the active D4 workspace. It absorbs the former high-level `README.md` guidance and points to the current canonical documents for architecture, deployment, workflow, and implementation skills.

## Project Overview

- **Product**: D4 is an AI-assisted automotive CRM built around FastAPI, SQLAlchemy, PostgreSQL, Jinja2 templates, and a mounted AI agent sub-application.
- **Primary runtime**: The canonical main web app lives in `web/backend/`, shared templates and static assets live in `web/frontend/`, messaging-specific runtime code lives in `web/message/`, shared uploads live in `web/app/static/uploads/`, the database layer lives in `db/`, and the AI assistant lives in `ai_agent/`.
- **Deployment entry points**: Vercel routes traffic through `api/index.py`, the full app runtime starts `web.backend.app.main:app` from `development`, and the dedicated relay runtime starts `web.message.backend.relay_app:app`.
- **AI surface**: The main FastAPI app mounts the AI sub-app at `/ai-agent`, which exposes its own `/api` routes and `/static` assets.
- **New agent surface**: The main FastAPI app also mounts the standalone `agent` sub-app at `/agent`, with its own `/api` routes, `/static` assets, and dashboard entry.

## Current Source of Truth

- `docs/agent.md`: project overview, documentation map, and governance.
- `docs/codex-working-rules.md`: Codex operating rules for reading scope, exclusions, reporting, and backups.
- `docs/testing.md`: active repo-level testing policy.
- `docs/skill.md`: implementation guidance for backend, frontend, and AI agent work.
- `docs/architecture.md`: active runtime architecture and request flow.
- `docs/deployment.md`: current Vercel, full-app runtime, and relay-only runtime deployment model.
- `docs/workflow.md`: phase numbering, artifact storage, and backup policy.
- `docs/erd.md`: current data model reference for active ORM entities.
- `docs/testing/`: canonical testing strategy, runbook, coverage matrix, and migration plan.
- `docs/SESSION_HANDOFF.md`: operational handoff snapshot; useful for current state, but not authoritative when it conflicts with the canonical docs above.

## Documentation Priority

- Treat `docs/*.md` as the primary D4 source of truth for runtime, workflow, architecture, UI, and delivery rules.
- Treat `docs/testing.md` as the active repository-wide testing policy.
- Treat `docs/testing/*.md` as the primary D4 source of truth for automated and manual validation.
- Treat `docs/skills/agency-agents/D4_USAGE.md` as the D4-specific guide for using imported skill libraries safely.
- Treat `docs/skills/**` as supplemental reference material, not product requirements.
- Treat imported `docs/skills/agency-agents/**` content as external playbooks and prompts. They can inform planning, but they never override D4 runtime docs or the actual codebase.

## Active Runtime Structure

- The current top-level folder layout is fixed. Do not move runtime, deployment, test, or documentation roots unless the user explicitly requests a structural migration and the docs are updated in the same phase.
- `api/index.py`: Vercel shim that adds `development` to `sys.path` and imports `web.backend.app.main:app`.
- `web/backend/app/main.py`: main FastAPI application, static mount, router registration, and `/ai-agent` mount point.
- `web/message/backend/relay_app.py`: relay-only FastAPI application for protected fixed-IP message handoff.
- `web/backend/app/api/`: route composition and object-specific routers.
- `web/backend/app/services/`: core business logic for CRM objects, messaging, search, dashboards, imports, and attachments.
- `web/frontend/templates/` and `web/frontend/static/`: server-rendered UI and shared front-end assets.
- `web/message/backend/` and `web/message/frontend/`: isolated messaging routers, services, providers, and templates.
- `db/database.py` and `db/models.py`: PostgreSQL engine setup, sessions, and ORM models.
- `ai_agent/llm/backend/`: AI reasoning, intent classification, provider fanout, and conversation context.
- `ai_agent/ui/backend/`: AI chat router, service orchestration, and integration.
- `ai_agent/ui/frontend/`: AI agent UI templates and static assets.
- `agent/llm/`: lightweight branding and assistant metadata for the standalone agent surface.
- `agent/ui/backend/`: standalone agent router, API endpoints, and UI service helpers.
- `agent/ui/frontend/`: standalone agent templates and static assets.
- `test/`: automated tests, manual verification assets, and test-specific notes.

## Technology Baseline

- **Framework**: FastAPI on Python 3.12.
- **Data layer**: SQLAlchemy with PostgreSQL via `psycopg`.
- **Rendering**: Jinja2 templates with vanilla CSS and JavaScript.
- **AI providers**: Cerebras and Groq are supported by the AI agent layer.
- **Testing**: `pytest`, `pytest-asyncio`, and `httpx`.

## Local Development Notes

- Install dependencies from the repository root with `pip install -r requirements.txt`.
- Set `DATABASE_URL` before starting the app. PostgreSQL is mandatory for the active runtime.
- Set `OPENAI_API_KEY`, `QDRANT_ENDPOINT`, and `QDRANT_API_KEY` before running the message-policy vector sync or live policy retrieval path.
- Run the Vercel-style entry from the repository root with `uvicorn api.index:app --reload`.
- Run the app directly from `development` with `uvicorn web.backend.app.main:app --reload`.

## Messaging Runtime Notes

- The `Send Message` screen is served by `/messaging/ui` and sends through the provider-based backend under `web/message/backend/`.
- `MessagingService.send_message()` resolves content, subject, template, and attachment metadata first, then dispatches through the active provider selected by `MESSAGE_PROVIDER`.
- `mock` is the safe local fallback, `slack` is the dev/test notification path, `surem` is the direct carrier delivery path, and `relay` forwards delivery to a protected runtime.
- `web.message.backend.relay_app` is the preferred deployment entry when the carrier requires a fixed or country-specific IP and the full app runtime must stay separate from the protected relay host.
- For developer verification, `slack` is the safest real external-delivery check because it exercises the outbound provider path without carrier-side allowlist risk.
- MMS images are stored in D4-managed storage first for preview, draft, and template reuse; when the active provider is SureM, the image is uploaded to SureM at final send time to obtain the carrier-facing image key.
- Every successful or failed send attempt writes a `MessageSend` history record so outbound activity remains visible in CRM history even when the provider rejects the message.
- Bulk send uses the same provider flow one contact at a time and records each attempt through the shared messaging service.
- SMS templates and SMS compose flows do not use a subject.
- Template/send content supports merge placeholders like `{Name}` and `{Model}`.
- SMS content over 90 bytes auto-upgrades to LMS at send time.
- LMS and MMS content must stay at or under 2000 bytes.
- D4 upload validation accepts JPG images up to 500KB for template and compose flows, and the active SureM MMS runtime uses that same 500KB ceiling.
- Messaging templates and message-send pages live under `web/message/frontend/templates/`, not under the shared `web/frontend/templates/` tree.
- `web/message/frontend/templates/messages/detail_view.html` avoids shared inline-pencil editing in the current runtime; use its object-level `Edit` / `Delete` actions instead of assuming every detail page exposes the shared inline edit affordances.
- Message-policy questions in the AI Agent now use a narrow vector-retrieval path backed by Qdrant and `learning/message_sending_rules_qdrant.json`.
- That policy knowledge path is retrieval-only. It does not replace the existing send-message action flow or broaden CRUD behavior.
- The policy index is designed for explicit sync through `MessagePolicyRetrievalService.sync_source_documents()` rather than boot-time auto-indexing, which keeps Vercel cold starts lighter and avoids hidden startup writes.

## Recommendation Runtime Notes

- The Home AI Recommend card and the Send Message AI Recommend flow share the same recommendation mode and the same sendable recommendation set.
- Users can change the recommendation mode either through the AI Agent chat or through the manual mode buttons on the Home sidebar card.
- `New Records` is the user-facing label for the fallback recommendation mode and means the most recently created sendable deals, ordered by newest first.
- `Follow Up` is the user-facing label for open opportunities with `is_followed=True`.
- `Closed Won` is the user-facing label for recently won opportunities.
- Running AI Recommend refreshes opportunity temperatures before rendering results: `Hot` for Test Drive, `Cold` for lost or older-than-30-day opportunities, and `Warm` for the rest.

## AI Agent Lead UX Notes

- Lead create now opens the actual lead create form inside the AI Agent conversation so the user can fill fields directly without a long prompt-by-prompt flow.
- The AI Agent workspace now promotes lead form content near the top of the agent body and embeds the actual web form screen for `/new-modal` flows so create/edit forms remain discoverable and behavior stays closer to the main web runtime.
- After lead save, AI Agent returns the user to the conversation with a clear success or failure message and the refreshed open-style lead context.
- Lead open and edit flows still prefer a chat-embedded pasted card inside the AI Agent conversation instead of relying on the separate workspace for the primary lead CRU path.
- When the user chooses lead `Edit` or asks to edit the active lead, AI Agent should open the actual lead edit form inline in the chat so the user can change fields immediately.
- Once a lead is in the active chat context, short field-only follow-ups such as `status Qualified` or `phone 01012345678` should continue the same lead edit flow without forcing the user to restate the record ID.
- Lead open cards should expose direct `Edit` and `Delete` actions so the user can jump straight into the in-chat edit or delete-confirmation flow.
- Requests like `show the lead I just created` or `방금 생성한 lead 보여줘` should resolve from the current conversation memory without needing another search step.
- The selection bar still exists, but lead `Open` and `Edit` actions now route into the pasted chat card pattern so the flow stays inside the conversation window.
- When a lead is deleted through the AI Agent flow, the success copy should prefer user-meaningful lead details such as name and phone instead of only the raw record ID.
- AI Agent lead lookup inputs such as brand, model, and product should accept human-readable names and resolve them before persistence; user-visible output should never expose lookup IDs.
- AI Agent debug instrumentation may be enabled from the header during testing, but it defaults to off and should remain an opt-in diagnostic aid rather than permanent visual noise.
- AI Agent code organization is moving toward strict `llm` (reasoning) and `ui` (orchestration) separation so intelligence engines and interactive flows can evolve with less cross-terminal conflict.
- Non-lead objects can still use the workspace fetch path when that remains the more natural UI.
- For AI Agent inline web-form flows, `brand`, `model`, `asset`, and `message_template` edit saves now follow the same AI-managed submit continuity pattern as the rolled-out chat surfaces, while still reusing the existing web form UI and validation rules.
- For AI Agent grouped-object chat cards and selection actions, `brand`, `model`, `asset`, and `message_template` `Edit` now opens the inline edit form directly instead of routing back through the generic open/manage path.
- AI Agent inline `message_template` forms apply a container-scoped type-visibility pass so `subject` and `image` fields follow the same SMS/LMS/MMS visibility rules even when the shared web modal script would otherwise bind too broadly.

## Ops Pilot Runtime Notes

- `Ops Pilot` is a separate dashboard-launched standalone agent surface.
- The dashboard entry loads its panel lazily through `/agent-panel`.
- The mounted runtime lives under `/agent`.
- The current standalone agent is a command-driven multi-object workspace rather than a lead-only CRUD shell.
- The standalone agent accepts plain-language commands such as `all leads`, `new contact`, `open opportunity 006...`, and `edit product 01t...`.
- The current supported objects are Lead, Contact, Opportunity, Asset, Product, Brand, and Model.
- The standalone agent reuses the existing D5 list, detail, and form routes inside its own embedded workspace instead of cloning object UIs into a second frontend stack.
- Lead create and edit still prefer `/leads/embedded-form` so the richer lead embedded runtime remains the source of truth.
- Non-lead create and edit flows currently open the existing modal-form routes inside the standalone agent workspace.
- The standalone agent frontend is intentionally independent from the existing AI Agent runtime so it can evolve on its own UI path.

## Mandatory Rules

### Architecture and Stability

- Keep modules small and responsibility-driven so one feature change does not destabilize unrelated flows.
- Keep routers thin and push business logic into services.
- Treat PostgreSQL as the only supported production database for active application behavior.

### Frontend Organization

- Keep templates organized by object or feature area under `web/frontend/templates/`.
- Keep JavaScript scoped to object or page behavior instead of adding global one-off scripts.
- Preserve the existing server-rendered UI model unless there is a clear architectural reason to change it.

### Field and Navigation Rules

- Avoid exposing raw lookup field labels with trailing `Id` or `ID` in the UI.
- Keep record names clickable in search, related lists, and recent-item surfaces.
- Default new fields to optional unless a real business rule requires otherwise.

### Display and Language Rules

- Render null-like values as blank output in the UI.
- Keep user-facing text, code comments, and documentation in English.
- Write code comments in clear English, and ensure commented code explains intent or non-obvious behavior unambiguously.
- Preserve the established Salesforce-inspired visual grammar across object pages.

### Error and State Management

- Surface recoverable errors to the UI cleanly instead of failing into raw server traces.
- Keep placeholders and unfinished features behind explicit user-friendly states.
- Preserve existing exception handling patterns in both the main app and AI agent paths.

## Documentation Rules

- Update `docs/agent.md`, `docs/skill.md`, `docs/architecture.md`, and `docs/deployment.md` when runtime behavior changes.
- Update `docs/codex-working-rules.md`, `docs/testing.md`, and `docs/ai-agent-crud-contract.md` when their policy surfaces change.
- Do not reintroduce retired `GEMINI.md` guidance as a parallel source of truth.
- Use the next unused phase number across `task/`, `Implementation/`, `Walkthrough/`, and `backups/` before writing artifacts.
- Store backups only for the module folders changed in the approved phase inside a dedicated grouped range folder such as `backups/001_100/phaseN/` or `backups/101_199/phaseN/`; do not leave phase backups as loose files at the backups root.
- Create new project-level markdown files under `development/docs/` by default.
- Keep root-level markdown files out of the repository root unless the file is a required phase artifact in `task/`, `Implementation/`, or `Walkthrough/`, or a folder-local README that documents a specific subtree.
- Read and follow all active markdown files under `development/docs/` before making project changes, but use this priority order when the volume is large: `docs/agent.md` -> `docs/codex-working-rules.md` -> `docs/testing.md` -> other task-relevant `docs/*.md` -> `docs/testing/*.md` -> D4-specific skill guides -> imported agency skill docs.
- If imported skill docs conflict with D4 runtime docs or the implemented code, follow the D4 docs and record the mismatch in active documentation rather than changing behavior blindly.

## Delivery Directives

- Save phase tracking files as `task/task_phaseN.md`, `Implementation/Implementation_phaseN.md`, and `Walkthrough/Walkthrough_phaseN.md`.
- Regardless of the magnitude of change, store a pre-change backup only for the modified modules under the matching grouped range folder, for example `backups/101_199/phase148/`, using phase-specific folders and relative paths.
- Do not create a broad or full-repository backup when the approved phase only changes a limited module set.
- When the Antigravity MCP `sequential-thinking` tool is available, use it for structured execution planning; if it is unavailable, do not block work and instead follow the docs-driven workflow automatically.

## Test and Cache Rules

- Before planning or running unit tests, read the canonical testing docs under `development/docs/testing/`.
- Use `development/.pytest_cache` as the canonical pytest cache location.
- Do not create or preserve duplicate pytest cache directories at the repository root, under `.gemini/`, or in other subfolders.
- Keep pytest cache directories ignored by git; they are local execution state and must not be committed.
- Keep the current folder layout intact: `api/`, `task/`, `Implementation/`, `Walkthrough/`, `vercel.json`, `render.yaml`, and `requirements.txt` stay at the repository root, while the active application code remains under `development/`.

## Design Principles

1. **Atomic first**: prefer independently testable modules, services, and UI units.
2. **Consistent detail views**: preserve standard tabs, related data surfaces, and responsive field grids.
3. **Traceable delivery**: store phase artifacts and backups for any meaningful documentation or code change.
4. **Documentation follows runtime**: deployment, architecture, and data model docs must reflect the live code path.

## Phase output storage rule

For every approved phase, maintain FOUR separate phase-labeled outputs with distinct purposes:

1. `Implementation/`

   * store the implementation record for the phase
   * summarize what was changed at a high level

2. `task/`

   * store the task/request record for the phase
   * include scope, approvals, and constraints

3. `Walkthrough/`

   * store the walkthrough/explanation for the phase
   * include what was done, how it works, and how to verify it

4. `backups/`

   * store backup copies only for changed module folders in that phase
   * do not back up untouched modules

Important:

* `Implementation/`, `task/`, and `Walkthrough/` are NOT backup folders.
* `backups/` is the backup folder.
* These four locations are separate deliverables and are not interchangeable.

Clarification on excluded folders:

* Do not inspect old historical contents in `Implementation/`, `task/`, `Walkthrough/`, or `backups/` unless needed for the current phase record.
* However, you MUST write new phase outputs to those folders for each approved phase.

Rules:

* For every implementation phase, create or update phase-labeled outputs in:

  * `Implementation/`
  * `task/`
  * `Walkthrough/`
  * `backups/`
* In `backups/`, save only the changed module folders for that phase.
* Do not treat `backups/` as a substitute for `Implementation/`, `task/`, or `Walkthrough/`.
* If earlier instructions were ambiguous, this rule is the source of truth going forward.
