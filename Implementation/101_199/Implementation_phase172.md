# Implementation Phase 172: AI Agent Architecture Refactoring (LLM vs UI)

## Goal
Restructure the AI Agent codebase into two distinct pillars: **`llm`** (the intelligence/reasoning layer) and **`ui`** (the presentation/integration layer). This organization improves modularity and prepares the "intelligence" core for standalone development or reinforcement learning.

## User Review Required
> [!IMPORTANT]
> This is a major structural change. While core logic remains the same, file paths and internal imports will change significantly across all AI Agent components.

## Proposed Changes

### 1. Directory Structure Adjustment
*   **LLM Pillar**: `.gemini/development/ai_agent/llm/backend/`
*   **UI Pillar**: 
    - `.gemini/development/ai_agent/ui/backend/`
    - `.gemini/development/ai_agent/ui/frontend/`

### 2. Migration Plan

#### [LLM Pillar: Backend Reasoning]
- [MOVE] `intent_preclassifier.py` -> `llm/backend/`
- [MOVE] `intent_reasoner.py` -> `llm/backend/`
- [MOVE] `conversation_context.py` -> `llm/backend/`
- [MOVE] `recommendations.py` -> `llm/backend/`

#### [UI Pillar: Backend Orchestration]
- [MOVE] `service.py` -> `ui/backend/`
- [MOVE] `router.py` -> `ui/backend/`
- [MOVE] `main.py` -> `ui/backend/`
- [MOVE] `ai_service.py` -> `ui/backend/`

#### [UI Pillar: Frontend Assets]
- [MOVE] `frontend/static/` -> `ui/frontend/static/`
- [MOVE] `frontend/templates/` -> `ui/frontend/templates/`

### 3. Cross-Module Updates
*   **Imports**: Update all `from ai_agent.backend...` to the new paths (e.g., `from ai_agent.llm.backend...` or `from ai_agent.ui.backend...`).
*   **Static Routes**: Update `ui/backend/main.py` to mount static files from the new `ui/frontend/static` path.
*   **Templates**: Update `ai_agent_panel.html` to reference script/link tags from the new locations (if paths changed at the web server level).

### 5. Documentation Updates
- Update `ai_agent/README.md` to reflect the new `llm` and `ui` pillar structure.
- Update `docs/agent.md` to outline the new architectural separation between reasoning and orchestration.

## Verification Plan
### Automated Tests
- Run `pytest` for Phase 170 tests (after updating their import paths) to ensure logic is still sound.
- Ensure `main.py` (now in `ui/backend`) starts and mounts all modules correctly.

### Manual Verification
- **PROHIBITED**: No manual testing.
