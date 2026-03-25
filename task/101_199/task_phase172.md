# Task Phase 172: AI Agent Architecture Refactoring (LLM vs UI)

## Objective
Split AI Agent into `llm` (reasoning) and `ui` (presentation) pillars.

## Detailed Tasks

### 1. Structure Preparation & Cleanup
- [ ] Remove incorrectly nested `llm/backend/frontend`.
- [ ] Create `ui/backend` and `ui/frontend` subdirectories.

### 2. Migration: LLM Pillar
- [ ] Move reasoning/intent files (`preclassifier`, `reasoner`, `context`, `recommendations`) to `llm/backend/`.
- [ ] Update internal cross-references within `llm/backend`.

### 3. Migration: UI Pillar (Backend)
- [ ] Move orchestration files (`service`, `router`, `main`, `ai_service`) to `ui/backend/`.
- [ ] Update imports to find `llm.backend` modules.

### 4. Migration: UI Pillar (Frontend)
- [ ] Move `static/` and `templates/` folders to `ui/frontend/`.
- [ ] Update `main.py` (Static mount) and `templates` (file paths).

### 5. Integration & Global Updates
- [ ] Update root `__init__.py` or any D4 integration points.
- [ ] Sync all unit tests to the new directory structure.

### 6. Documentation Sync
- [ ] Rewrite `ai_agent/README.md` to describe `llm` vs `ui` pillars.
- [ ] Update `docs/agent.md` to reflect the new intelligence architecture.

## Verification
- [ ] Run `pytest` on all updated AI Agent unit tests.
- [ ] Verify `main.py` starts without import errors.
