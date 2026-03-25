# Task: Phase 41 - Multi-LLM API Integration & Test Suite Stabilization

## Objective
Integrate the new `ChatGPT_API_Key` and `Gemini_API_Key` provided in the `.env` file into the AI Agent's ensemble logic. Conduct a comprehensive unit test sweep across the entire project and fix any regressions or path issues caused by the recent folder reorganization.

## Sub-tasks
1. **API Integration**:
   - Update `ai_agent/backend/service.py` to support custom environment variable names: `ChatGPT_API_Key` and `Gemini_API_Key`.
   - Ensure the ensemble logic correctly utilizes these providers alongside Groq and Cerebras.
2. **Environment Stabilization**:
   - Install `psycopg[binary]` to support PostgreSQL connections defined in the `.env` file.
   - Update `db/database.py` to use a local SQLite database automatically during unit tests (`pytest`), preventing remote authentication errors.
3. **Test Suite Repair**:
   - Update hardcoded database paths in unit tests (e.g., `test_contacts.py`, `test_crm.py`) to the new `./db/test_runs/` directory.
   - Fix HTML template paths in `test_pencil_unity.py` to point to the consolidated `frontend/templates/` folder.
4. **Full Validation**:
   - Execute the complete unit test suite (`pytest test/unit/`).
   - Achieve 100% pass rate for all active tests.

## Completion Criteria
- AI Agent supports the new Gemini and ChatGPT API keys.
- Unit tests are isolated from the remote PostgreSQL database.
- 102+ tests pass successfully.
- Phase 41 documentation is generated.