# Phase 117 Walkthrough

## Result

- The AI Agent header now includes `ENG` and `KOR` buttons.
- The selected language updates the trigger label, subtitle, quick guide, welcome tips, selection buttons, and input placeholder, and is passed through chat requests as `language_preference`.
- The no-selection Send Message guidance now returns Korean copy when the AI Agent is set to Korean.
- The language toggle is hidden when the AI Agent is minimized.

## Validation

- `PYTHONPATH=.gemini/development pytest -o cache_dir=.gemini/development/.pytest_cache .gemini/development/test/unit/ai_agent/backend/test_intent_variations.py .gemini/development/test/unit/ai_agent/frontend/test_assets.py`
- Result: `42 passed`
- Live checks:
  - dashboard HTML includes `ai-agent-lang-eng` and `ai-agent-lang-kor`
  - `Send Message` with `language_preference=kor` returns Korean guidance
