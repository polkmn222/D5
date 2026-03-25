# Implementation Plan - Phase 154: AI Agent Granular Refactoring & Modularization

## Goal
Refactor the AI Agent's monolithic structure into a highly granular, feature-based architecture. This involves reorganizing directories to prioritize functionality and splitting large service/JS files into object-specific modules to ensure stability, maintainability, and multi-terminal development compatibility.

## Proposed Directory Structure
```
.gemini/development/ai_agent/
├── objects/
│   ├── account/
│   │   ├── backend/
│   │   └── frontend/
│   ├── contact/
│   │   ├── backend/
│   │   └── frontend/
│   ├── asset/
│   │   ├── backend/
│   │   └── frontend/
│   ├── product/
│   │   ├── backend/
│   │   └── frontend/
│   ├── lead/
│   │   ├── backend/
│   │   └── frontend/
│   ├── opportunity/
│   │   ├── backend/
│   │   └── frontend/
│   └── message_template/
│       ├── backend/
│       └── frontend/
├── recommend/
│   ├── backend/
│   └── frontend/
├── messaging/
│   ├── backend/
│   └── frontend/
└── llm/
    ├── backend/
    └── frontend/
```

## Backend Refactoring (Python)
- **Modularization**: Split `.gemini/development/ai_agent/backend/service.py` into feature-specific services.
- **Class Structure**: Each service will be a class with `@staticmethod` as per project standards.
- **LLM Core**: Move common LLM interaction logic (API calls to Cerebras, Groq, Gemini) to `llm/backend/service.py`.
- **Object Services**: Each object (e.g., Lead, Contact) will have its own `service.py` in its respective `objects/<name>/backend/` folder.
- **Stability**: Ensure each module is independent to prevent cascading failures.

## Frontend Refactoring (JS/HTML)
- **JS Modularization**: Split `.gemini/development/ai_agent/frontend/static/js/ai_agent.js` into object-specific JS files.
- **Template Folderization**: Move templates to feature-specific `frontend/templates/` folders.
- **Schema Management**: Decentralize `AGENT_TABLE_SCHEMAS` and `AGENT_TABLE_LABELS` so each object defines its own display logic.

## Steps
1. **Research & Map**: Identify all object-specific logic in `service.py` and `ai_agent.js`.
2. **Directory Setup**: Create the new granular folder structure.
3. **Core LLM Migration**: Extract and move base LLM logic to `llm/backend/`.
4. **Object Logic Migration**: Iteratively move Lead, Contact, etc., logic to their new homes.
5. **Frontend Splitting**: Refactor the main JS file into modules.
6. **Integration**: Update imports and references to point to new locations.
7. **Validation**: Run unit tests for each service.
8. **Backup**: Save all changed files to `backups/phase154/`.

## Verification Plan
- **Unit Tests**: Create/update tests for each new service module.
- **UI Check**: Ensure the AI Agent panel still functions correctly and displays all objects as expected.
- **Zero Korean Policy**: Verify no Korean text exists in new or refactored files.
