# Phase 129 Walkthrough

## Result

- `Hot Deals`, `Closed Won`, and `New Records` are now all constrained to the most recent 7 days.
- `Follow Up` remains based on `is_followed = true` for open opportunities only.

## Validation

- `PYTHONPATH=.gemini/development pytest -o cache_dir=.gemini/development/.pytest_cache .gemini/development/test/unit/ai_agent/backend/test_recommend_logic.py .gemini/development/test/unit/ai_agent/backend/test_recommend_mode.py`
- Result: `11 passed`
