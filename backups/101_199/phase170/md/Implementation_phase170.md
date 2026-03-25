# Implementation Phase 170: English Intent & Context Robustness

## Goal
Strengthen the AI Agent's ability to handle natural, informal, and error-prone English input. Focus on "human-like" mannerisms, common typos, and seamless multi-turn context resolution.

## Proposed Changes

### 1. Intent & Object Mapping Refinement
#### [MODIFY] [intent_preclassifier.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/backend/intent_preclassifier.py)
*   **Expand `TYPO_MAP`**: Add common English slips (e.g., `oportunity`, `opp`, `contax`, `templt`, `leads'`).
*   **Expand `ACTION_` sets**: Add informal verbs like `grab`, `fetch`, `tweak`, `dump`, `nuke`, `fix`.
*   **Possessive Handling**: Update `normalize` or `detect` to handle `'s` (e.g., `John's lead` -> `lead John`).

### 2. Conversational Context Enhancements
#### [MODIFY] [service.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/ai_agent/backend/service.py)
*   **Improve `_resolve_contextual_record_reference`**: Ensure it handles pronouns (`it`, `them`, `that one`, `those`) more aggressively by looking at the last 1-2 objects in context.
*   **Ambiguity Resolution**: If a user says "Update it" and the last object was a lead, automatically target that lead without asking for clarification.

### 3. Verification Suite
#### [NEW] [test_english_robustness.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/test/unit/ai_agent/backend/test_english_robustness.py)
*   Test informal phrasing: "Grab the leads", "Nuke that opportunity", "Tweak his email".
*   Test typos: "Show lds", "Updt contax".
*   Test possessives: "Check Kim's status".

#### [NEW] [test_context_recall.py](file:///Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development/test/unit/ai_agent/backend/test_context_recall.py)
*   Test multi-turn pronoun resolution: "Show leads" -> "Open the third one" -> "Delete it".

## Verification Plan

### Automated Tests
*   `pytest .gemini/development/test/unit/ai_agent/backend/test_english_robustness.py`
*   `pytest .gemini/development/test/unit/ai_agent/backend/test_context_recall.py`
