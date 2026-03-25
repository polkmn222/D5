# Task Phase 168: Salesforce Icons and Server-side Search Implementation

## Objective
1. Update "Select All" and "Clear All" buttons with Salesforce-style icons.
2. Implement server-side search in the data table (search across all records).

## Detailed Tasks
### 1. Salesforce-style Icons
- **File:** `.gemini/development/ai_agent/frontend/static/js/ai_agent.js`
    - Update "Select All" and "Clear All" buttons with `✓` and `✕` icons.
- **File:** `.gemini/development/ai_agent/frontend/static/css/ai_agent.css`
    - Style the icon buttons to be compact and aligned.

### 2. Server-side Search
- **File:** `.gemini/development/ai_agent/frontend/static/js/ai_agent.js`
    - Implement `handleAgentTableSearch` to detect "Enter" key.
    - Implement `requestAgentSearch` to call the backend with a search query.
- **File:** `.gemini/development/ai_agent/backend/service.py`
    - Enhance `_execute_intent` and `_sanitize_pagination` to handle search terms if provided.
    - Implement a rule-based search extraction if LLM is not available.

## Verification
- Unit test to verify server-side search SQL generation.
- Existing AI Agent tests should pass.
