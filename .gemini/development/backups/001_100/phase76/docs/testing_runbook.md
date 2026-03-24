# Testing Runbook

## Default Review Order

1. `docs/agent.md`
2. `docs/workflow.md`
3. `docs/spec.md`
4. `docs/testing/README.md`
5. `docs/testing/strategy.md`

## Current Practical Commands

- Full unit suite: `PYTHONPATH=.gemini/development pytest .gemini/development/test/unit`
- Non-AI, non-send-message focused suite: run the selected CRM and shared UI files explicitly
- Integration: `PYTHONPATH=.gemini/development pytest .gemini/development/test/integration`

## Recommended Future Commands After Migration

- Core CRM objects: `pytest .gemini/development/test/unit/crm`
- Shared UI: `pytest .gemini/development/test/unit/ui`
- Search: `pytest .gemini/development/test/unit/search`
- Messaging: `pytest .gemini/development/test/unit/messaging`
- AI agent: `pytest .gemini/development/test/unit/ai_agent`

## Migration Order

1. Create shared fixture and factory modules.
2. Move shared UI and search tests first.
3. Move core CRM object tests.
4. Move messaging tests.
5. Move AI agent tests.
6. Move or retire legacy phase-named tests.
