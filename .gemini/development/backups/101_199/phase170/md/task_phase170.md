# Task Phase 170: English Intent & Context Robustness

## Objective
Strengthen English language handling (typos, slang, mannerisms) and multi-turn context recall.

## Detailed Tasks

### 1. English Intent & Synonym Expansion
- **File:** `.gemini/development/ai_agent/backend/intent_preclassifier.py`
- [ ] Research common Salesforce-user slang and typos for CRM objects.
- [ ] Expand `TYPO_MAP` with `opp`, `contax`, `leadz`, etc.
- [ ] Expand `ACTION_` sets with `grab`, `nuke`, `tweak`, `fix`.
- [ ] Add logic to strip possessive `'s` in `normalize`.

### 2. Context Recall & Pronoun Resolution
- **File:** `.gemini/development/ai_agent/backend/service.py`
- [ ] Enhance `_resolve_contextual_record_reference` for `it`, `them`, `those`.
- [ ] Ensure `last_object` and `last_record_id` are used for "Update it" styles.

### 3. Robustness Testing
- **File:** `.gemini/development/test/unit/ai_agent/backend/test_english_robustness.py`
- [ ] Test: "Grab the leads for Kim"
- [ ] Test: "Nuke that opp"
- [ ] Test: "Tweak the status"
- **File:** `.gemini/development/test/unit/ai_agent/backend/test_context_recall.py`
- [ ] Test chain: `Show leads` -> `Select it` -> `Delete it`.

## Verification
- [ ] Run robustness tests via `pytest`.
- [ ] Verify contextual resolution for complex multi-turn dialogues.
