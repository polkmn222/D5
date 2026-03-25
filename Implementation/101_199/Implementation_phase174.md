# Implementation Plan - AI Agent Lead Table Fix (Phase 174)

This plan addresses the issue where `display_name` and `model` fields are missing from the Lead table in the AI Agent UI.

## Proposed Changes

### AI Agent Backend
#### [MODIFY] [service.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/ui/backend/service.py)
- Update `_default_query_parts("lead")` to:
    - Include `first_name || ' ' || last_name AS display_name` in the `select` statement.
    - Join with the `models` table (`LEFT JOIN models m ON l.model = m.id`) to get the model name.
    - Include `m.name AS model` in the `select` statement.
    - Update `from` and `where` clauses to use table aliases (`l` for leads).
- Update `_apply_search_to_sql("lead", ...)` to use the `l` alias for search fields.

## Verification Plan

### Automated Tests
- Create a new unit test `test_lead_join_phase174.py` in `.gemini/development/test/unit/ai_agent/backend/` to verify:
    - `_default_query_parts("lead")` contains the display_name concatenation.
    - `_default_query_parts("lead")` contains the model name join.
    - `_apply_search_to_sql("lead", ...)` uses the correct table aliases.
- Run tests using `pytest`:
    ```bash
    pytest .gemini/development/test/unit/ai_agent/backend/test_lead_join_phase174.py
    ```

### Manual Verification
- **None** (Per instructions: manual test is strictly forbidden)
