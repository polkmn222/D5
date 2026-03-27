# Known Test Status

This file tracks tests that are known to have special behavior, skip conditions, or were updated for specific reasons.

## Phase 169 Changes

| Test | Status | Reason |
|---|---|---|
| `test_lead_update_returns_view_card` | Updated | Changed from `process_query` (LLM-path, non-deterministic) to `_execute_intent` (deterministic). LLM may classify `update lead TEST_FLOW_LEAD ...` differently based on model used. Core behavior is now tested reliably. |

## Phase 211 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py` | Added | Frontend-focused contract coverage now asserts that AI Agent workspace content is promoted near the top of the agent body, scrolled into view, and keeps debug mode opt-in by default. |
| `development/test/unit/ai_agent/backend/test_lead_crud_module.py` | Updated | The AI Agent `/new-modal` runtime contract now embeds the actual web form screen in a workspace iframe rather than cloning the form body into a custom workspace renderer. |

## Phase 213 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_runtime_contract.py` | Added | Covers the new standalone `agent` mount, dashboard panel fragment route, and core service payload helpers. |
| `development/test/unit/agent/test_frontend_contract.py` | Added | Covers the new dashboard button, standalone panel template, frontend CRUD endpoint usage, and core layout styling. |

## Phase 214 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the standalone agent first-load open path, busy-state recovery for save/load flows, and explicit delete confirmation behavior. |

## Phase 215 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the standalone agent request timeout helper and the post-save asynchronous refresh path so save flows do not appear stuck indefinitely. |

## Phase 216 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the lead-first shell contract where the standalone agent embeds the real `/leads/new-modal` web form route instead of using a custom standalone lead form. |

## Phase 217 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the near-fullscreen Ops Pilot layout and iframe auto-resize contract so the embedded web lead create/edit screen is not clipped as aggressively inside the agent shell. |

## Phase 218 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the fixed workspace shell with internal iframe scrolling so the embedded web lead form stays scrollable without auto-growing the entire agent panel. |

## Phase 219 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the standalone agent contract that opens the shared lead form in `embedded=1` mode instead of a plain modal fragment path. |
| `development/test/unit/web/backend/app/api/test_form_router_modals.py` | Updated | Covers the shared lead form embedded mode so lookup containers still render while modal-only close controls and body height limits are removed for agent embedding. |

## Phase 220 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the standalone agent contract that opens a dedicated embedded lead page instead of a bare modal fragment URL. |
| `development/test/unit/web/backend/app/api/test_form_router_modals.py` | Updated | Covers the dedicated embedded lead page contract so the shared lead form is rendered together with lookup assets inside the iframe runtime. |

## Phase 221 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_runtime_contract.py` | Updated | Covers the standalone agent lead detail payload used to render an AI Agent-style open card after save. |
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the post-save AI Agent-style open card and embedded cancel bridge in the standalone agent shell. |
| `development/test/unit/web/backend/app/api/test_form_router_modals.py` | Updated | Covers the embedded form footer contract where `Save & New` is replaced by a cancel bridge back to the standalone agent shell. |

## Phase 222 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers iframe pending-state hiding during save redirects and auto-scrolling the standalone agent workspace toward the latest interaction state. |

## Phase 223 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the iframe `about:blank` bootstrap-load guard and the pending-state recovery path so New/Edit embedded forms do not remain hidden before the real page loads. |

## Phase 225 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/agent/test_runtime_contract.py` | Updated | Replaced the lead-only Ops Pilot contract with the new standalone multi-object command parser and bootstrap payload contract. |
| `development/test/unit/agent/test_frontend_contract.py` | Updated | Covers the new command shell, transcript area, object quick actions, and iframe workspace contract under `development/agent/`. |
| `development/test/unit/agent/test_router.py` | Updated | Covers the new `/agent/api/bootstrap` and `/agent/api/command` endpoints for deterministic command routing. |

## Phase 226 Changes

| Test | Status | Reason |
|---|---|---|
| `development/test/unit/web/frontend/test_crm_list_view_contract.py` | Added | Covers shared CRM list-view contracts for lead/contact list shells, list-view controls, selection, bulk-delete affordances, and empty-state behavior. |
| `development/test/unit/web/frontend/test_crm_detail_view_contract.py` | Added | Covers shared CRM detail-page action contracts, inline-edit affordances, related-tab presence, and related-card empty-state behavior. |
| `development/test/unit/web/frontend/test_related_list_contract.py` | Added | Covers the shared related-list page contract for Back/New actions, first-column links, optional Actions column, and currency rendering. |
| `development/test/unit/web/frontend/test_trash_dom_contract.py` | Added | Covers recycle-bin DOM behavior including search, empty state, load-more indicator, and permanent-delete confirmation contract. |
| `development/test/unit/web/frontend/test_bulk_action_js.py` | Added | Covers shared bulk-delete JavaScript behavior for checkbox selection, delete-button state, confirmation, and shared endpoint wiring. |
| `development/test/unit/web/backend/app/api/test_trash_router.py` | Added | Covers recycle-bin router behavior for template rendering, error redirect handling, restore redirect, and permanent-delete failure redirect. |
| `development/test/unit/web/frontend/test_ui_js_logic.py` | Updated | Expanded shared frontend JS coverage to include list-view persistence hooks, bulk-delete wiring, and trash list search/windowing behavior. |
| `development/test/unit/web/frontend/test_gk_design_system.py` | Updated | Expanded shared web template coverage for related-list and recycle-bin DOM contracts in addition to existing list-view design checks. |
| `development/test/unit/web/backend/app/api/test_form_router_modals.py` | Updated | Expanded modal-route contract coverage for shared CRM create/edit routes and related-create lookup-prefill behavior. |

## Current Full Unit Reference

- Command: `PYTHONPATH=development pytest development/test/unit -rs -q`
- Last reviewed status: `337 passed`

## Current Focused Reference

- Command: `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest development/test/unit/ai_agent/backend/test_search_concatenation_phase175.py development/test/unit/ai_agent/backend/test_lead_join_phase174.py development/test/unit/ai_agent/backend/test_opportunity_join.py development/test/unit/ai_agent/backend/test_lead_crud_normalization_phase184.py development/test/unit/ai_agent/backend/test_phase183.py development/test/unit/ai_agent/frontend/test_responsive_ui_css.py development/test/unit/web/message/backend/test_message_template_limits.py -q`
- Last reviewed status: `29 passed`
- Command: `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest development/test/unit/ai_agent/backend/test_lead_crud_logic_phase171.py development/test/unit/ai_agent/backend/test_lead_crud_logic_phase177.py development/test/unit/ai_agent/backend/test_lead_flow_consistency.py development/test/unit/ai_agent/backend/test_phase180.py development/test/unit/web/message/backend/test_message_send_limits.py -q`
- Last reviewed status: `15 passed, 1 warning`
- Command: `PYTHONPATH=development pytest development/test/unit/ai_agent/backend/test_lead_crud_module.py development/test/unit/ai_agent/frontend/test_responsive_ui_css.py development/test/unit/ai_agent/frontend/test_workspace_visibility_contract.py -q`
- Last reviewed status: `29 passed`
- Command: `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py -q`
- Last reviewed status: `9 passed`
- Command: `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py -q`
- Last reviewed status: `12 passed`
- Command: `DATABASE_URL=sqlite:///:memory: PYTHONPATH=development pytest development/test/unit/web/frontend/test_ui_js_logic.py development/test/unit/web/frontend/test_gk_design_system.py development/test/unit/web/backend/app/api/test_form_router_modals.py development/test/unit/web/backend/app/api/test_trash_router.py development/test/unit/web/frontend/test_trash_dom_contract.py development/test/unit/web/frontend/test_crm_list_view_contract.py development/test/unit/web/frontend/test_crm_detail_view_contract.py development/test/unit/web/frontend/test_related_list_contract.py development/test/unit/web/frontend/test_bulk_action_js.py -q`
- Last reviewed status: `42 passed`
- Command: `PYTHONPATH=development pytest development/test/unit/agent/test_runtime_contract.py development/test/unit/agent/test_frontend_contract.py -q`
- Last reviewed status: `12 passed`

## Current Provider Verification Note

- Slack provider verification succeeded for an automated MMS-style send path in phase 190.
- Solapi MMS carrier verification is currently blocked by Solapi IP allowlist rejection until the active runtime egress IP is registered.
- Runtime provider diagnostics are now exposed through `/messaging/provider-status` for deployment verification.

## Current State

- There are no currently recorded failing or skipped unit tests in the canonical full-suite run.
- The mismatches documented in phase 135 and early phase 136 were resolved by aligning tests and test docs to the current runtime contract without changing runtime code.
- The current shared `web` contract baseline now includes focused unit / DOM-style coverage for shared CRM list/detail/related/trash surfaces, bulk-delete JavaScript, and recycle-bin router behavior outside `ai_agent`.

## Historical Notes

- Messaging UI tests now account for the split template roots under `web/message/frontend/templates/`.
- The message-send detail page is tested as a non-inline-edit exception: it exposes object-level `Edit` / `Delete` actions without shared pencil-based inline editing.
- SMS template subject expectations, AI selection payload normalization, and direct-call router signatures are now reflected in the unit suite.

## Usage Rule

- Use this file to document known test mismatches while docs, tests, and runtime behavior are being brought back into alignment.
- Do not treat entries here as permanent waivers; remove or update them when the runtime or tests are corrected.
