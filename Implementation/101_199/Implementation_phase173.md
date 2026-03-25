# Implementation Plan - Phase 173: API Key Removal

This plan outlines the complete removal of Gemini and ChatGPT (OpenAI) API dependencies from the AI Agent codebase.

## Proposed Changes

### AI Agent Backend

#### [MODIFY] [service.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/backend/service.py)
- **Delete Methods**:
  - `_call_gemini`
  - `_call_openai`
- **Update `_call_multi_llm_ensemble`**:
  - Remove logic referencing `GEMINI_API_KEY` and `OPENAI_API_KEY`.
  - Remove calls to `cls._call_gemini` and `cls._call_openai`.
- **Update `_execute_intent` (USAGE)**:
  - Remove Gemini and OpenAI links from the usage information text.

### Dependencies

#### [MODIFY] [requirements.txt](file:///Users/sangyeol.park@gruve.ai/Documents/D4/requirements.txt)
- [DELETE] `openai`
- [DELETE] `google-generativeai`

### Documentation

#### [MODIFY] Documentation in `docs/`
- Remove mentions of Gemini and ChatGPT API keys from architectural diagrams or setup guides (specifically checking Phase 41 related docs).

## Verification Plan

### Automated Tests
- Create `test_api_key_removal_phase173.py`:
  - Verify `_call_multi_llm_ensemble` no longer attempts to call Gemini or OpenAI.
  - Verify `USAGE` response text is updated.
  - Ensure Cerebras and Groq fallbacks still function correctly.
- Run existing chat flow tests to ensure no regressions.

### Manual Verification
- **None** (Strictly prohibited).
