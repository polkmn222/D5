# Phase 173: API Key Removal and Codebase Cleanup

This phase focuses on removing external AI dependencies (Gemini, ChatGPT) from the AI Agent to streamline the codebase and eliminate unused API key references.

## Research & Planning
- [x] Identify all `GEMINI_API_KEY` and `OPENAI_API_KEY` occurrences
- [x] Map out `service.py` methods for removal (`_call_gemini`, `_call_openai`, etc.)
- [x] Identify documentation files for cleanup (Phase 41, etc.)
- [x] Verify dependency status in `requirements.txt`

## Documentation
- [x] Create/Update `implementation_plan.md` (Phase 173)
- [ ] Create `Implementation_phase173.md` (Self-contained artifact)
- [ ] Create `task_phase173.md` (Self-contained artifact)

## Implementation
- [ ] Remove Gemini/OpenAI call methods in `service.py`
- [ ] Update `_call_multi_llm_ensemble` to exclude removed models
- [ ] Remove `openai` and `google-generativeai` from `requirements.txt`
- [ ] Clean up documentation in `docs/` folder

## Verification
- [ ] Create `test_api_key_removal_phase173.py`
- [ ] Ensure ensemble logic still works with Cerebras/Groq
- [ ] Verify `USAGE` intent response update
- [ ] Finalize `walkthrough_phase173.md`

## Finalization
- [ ] Backup modified files to `backups/phase173`
