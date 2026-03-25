# Phase 111 Implementation

## Changes

- Updated `.gemini/development/ai_agent/backend/recommendations.py` so the user-facing fallback recommendation label is now `New Records`, while still keeping backward compatibility with the internal `Default` mode.
- Increased the shared sendable recommendation limit and applied it to both Home and Send Message via `.gemini/development/web/backend/app/services/dashboard_service.py`, `.gemini/development/web/backend/app/api/routers/dashboard_router.py`, and `.gemini/development/web/message/backend/router.py`.
- Updated `.gemini/development/web/frontend/templates/dashboard/dashboard.html` and `.gemini/development/web/frontend/templates/dashboard/dashboard_ai_recommend_fragment.html` so the Home card shows `New Records` and renders the recommendation table inside a scrollable shell.
- Updated `.gemini/development/ai_agent/backend/service.py` and `.gemini/development/docs/agent.md` so AI Agent and docs explain `New Records` as the newest sendable deals.
- Extended recommendation tests to cover the renamed label and scrollable table behavior.

## Result

- Users now see `New Records` instead of `Default`, and the AI Recommended Deals table can show more than five deals with scroll support when more sendable recommendations exist.
