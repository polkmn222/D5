# Phase 115 Walkthrough

## Result

- `Hot Deals` now shows only `Test Drive` opportunities.
- `Follow Up` now shows only open opportunities with `is_followed=True`.
- `Closed Won` replaces `Closing Soon` and shows recently won opportunities.
- `New Records` excludes won/lost opportunities.
- Running AI Recommend now refreshes opportunity temperature values before rendering the table.

## Validation

- `PYTHONPATH=.gemini/development pytest -o cache_dir=.gemini/development/.pytest_cache .gemini/development/test/unit/ai_agent/backend/test_recommend_logic.py .gemini/development/test/unit/ai_agent/backend/test_recommend_mode.py .gemini/development/test/unit/dashboard/test_recommendation_fragment.py .gemini/development/test/unit/ai_agent/frontend/test_assets.py`
- Result: `16 passed`
- Live checks:
  - `POST /api/recommendations/mode` works for `Hot Deals`, `Follow Up`, `Closed Won`, and `New Records`
  - dashboard contains `Follow Up` and `Closed Won`
  - dashboard no longer contains `Closing Soon`
