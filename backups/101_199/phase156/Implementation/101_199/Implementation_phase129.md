# Phase 129 Implementation

## Changes

- Updated `.gemini/development/ai_agent/backend/recommendations.py` so `New Records` now uses the same 7-day window style as `Hot Deals` and `Closed Won`.
- Kept `Follow Up` limited to `Opportunity.is_followed == True` and open opportunities only.
- Extended `.gemini/development/test/unit/ai_agent/backend/test_recommend_logic.py` to ensure older-than-7-day opportunities are excluded from `New Records`.

## Result

- AI Recommend now follows the requested rule set:
  - `Hot Deals` -> Test Drive within 7 days
  - `Closed Won` -> Closed Won within 7 days
  - `New Records` -> open non-won/non-lost opportunities within 7 days
  - `Follow Up` -> followed open opportunities
