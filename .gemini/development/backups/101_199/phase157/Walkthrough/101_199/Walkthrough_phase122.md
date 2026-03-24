# Phase 122 Walkthrough

## Result

- Home no longer preloads AI recommendations.
- Home no longer preloads the full AI Agent panel.
- `Start Recommend` now remains the only path that loads recommendations.
- `Ask AI Agent` now fetches the panel markup on demand.

## Validation

- `PYTHONPATH=.gemini/development pytest -o cache_dir=.gemini/development/.pytest_cache .gemini/development/test/unit/dashboard/test_recommendation_fragment.py .gemini/development/test/unit/ai_agent/frontend/test_assets.py`
- Result: `8 passed`
- Local timing check after restart:
  - `/` -> about `0.775s`
  - `/api/recommendations` -> about `3.46s`
  - `/ai-agent-panel` -> about `0.006s`
