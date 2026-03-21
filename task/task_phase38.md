# Task: Phase 38 - AI Agent Intent Debugging & Consistency

## Objective
Investigate and fix the issue where leads created via natural language were not being correctly persisted or retrieved. Enhance the AI Agent's conversational memory and bilingual name mapping to ensure a smooth "Create -> Query" workflow.

## Sub-tasks
1. **Source Backup**: Create a full backup of AI Agent service logic in `.gemini/development/backups/phase38/`.
2. **Reproduction & Debugging**:
   - Create `test_ai_lead_debug.py` to simulate the reported failure: "박상열 리드 생성" followed by "상태 선택" and "조회".
   - Identify that the agent needs explicit instructions to map single-word responses (e.g., "new") to the current context.
3. **Prompt Optimization**:
   - Update `AiAgentService` system prompt to include a `CONVERSATIONAL CONTEXT` section.
   - Mandate that single-word inputs be interpreted based on previous turns.
   - Standardize Korean name mapping (e.g., mapping "박상열" to `last_name` when `first_name` is ambiguous).
   - Refine `QUERY FLOW` to prioritize `created_at DESC` for "just created" records.
4. **Validation via Testing**:
   - Run a comprehensive test battery including `test_ai_agent_crud.py`, `test_ai_agent_auto.py`, and the new debug test.
   - Ensure 100% pass rate for conversational CRUD across all objects.

## Completion Criteria
- Comprehensive backup for Phase 38 is created.
- AI Agent successfully handles multi-turn creation flows (Incomplete -> Complete -> Created).
- "방금 생성된 리드 조회" correctly returns the latest record using optimized SQL.
- Phase 38 documentation is generated.