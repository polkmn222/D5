# Task List - Phase 154: AI Agent Granular Refactoring

## 1. Directory Structure Setup [ ]
- [ ] Create `ai_agent/objects/` folder
- [ ] Create subfolders for each object (Account, Contact, Asset, Product, Lead, Opportunity, Message Template)
- [ ] Create `backend/` and `frontend/` subfolders for each object
- [ ] Create `ai_agent/llm/` (with `backend/` and `frontend/`)
- [ ] Create `ai_agent/recommend/` (with `backend/` and `frontend/`)
- [ ] Create `ai_agent/messaging/` (with `backend/` and `frontend/`)

## 2. Backend Modularization [ ]
- [ ] Extract base LLM logic to `llm/backend/service.py`
- [ ] Extract Lead logic to `objects/lead/backend/service.py`
- [ ] Extract Contact logic to `objects/contact/backend/service.py`
- [ ] Extract Opportunity logic to `objects/opportunity/backend/service.py`
- [ ] Extract Product logic to `objects/product/backend/service.py`
- [ ] Extract Asset logic to `objects/asset/backend/service.py`
- [ ] Extract Message Template logic to `objects/message_template/backend/service.py`
- [ ] Refactor `AiAgentService` to delegate to these specific services.

## 3. Frontend Modularization [ ]
- [ ] Split `ai_agent.js` into object-specific JS modules.
- [ ] Move HTML templates to object-specific `frontend/templates/` folders.
- [ ] Update frontend references to load new JS modules.

## 4. Documentation & Cleanup [ ]
- [ ] Create `Walkthrough_phase154.md`
- [ ] Verify zero Korean text.
- [ ] Backup all changed files to `backups/phase154/`.

## 5. Verification [ ]
- [ ] Run unit tests for each refactored service.
- [ ] Verify AI Agent functionality in UI.
