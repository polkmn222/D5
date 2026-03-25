# Phase 117 Implementation

## Changes

- Added an `ENG` / `KOR` language toggle to the AI Agent header in `.gemini/development/ai_agent/frontend/templates/ai_agent.html`.
- Updated `.gemini/development/ai_agent/frontend/static/js/ai_agent.js` to persist the chosen language, localize the trigger label, subtitle, quick guide, selection actions, welcome tips, input placeholder, and send-message guidance, and send `language_preference` with chat requests.
- Updated `.gemini/development/ai_agent/frontend/static/css/ai_agent.css` so the language toggle hides automatically when the AI Agent is minimized.
- Updated `.gemini/development/ai_agent/backend/router.py` and `.gemini/development/ai_agent/backend/service.py` so the backend receives the UI language preference and uses it for the no-selection Send Message guidance plus LLM prompt steering.
- Extended AI Agent tests to cover the new header buttons, request payload, localized guidance, and language-toggle styling.

## Result

- Users can now explicitly switch the AI Agent between English and Korean without relying only on automatic language detection.
