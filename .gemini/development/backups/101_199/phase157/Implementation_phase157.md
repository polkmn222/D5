# Implementation Plan - Phase 157: AI Recommendation Consistency and UI Refinement

## Goal
1.  Restore and refine the AI recommendation logic for updating opportunity temperature.
2.  Ensure AI recommendation consistency across all entry points (Home, Send Message, AI Agent).
3.  Refine the UI feedback during AI recommendation mode selection in the Send Message tab.

## Detailed Requirements
### 1. Temperature Update Logic
- In `AIRecommendationService.refresh_opportunity_temperatures`, check `updated_at` and `updated_by`.
- **Condition**: If `updated_at` is today AND `updated_by` is 'AI Recommend' (aliased as 'ai agent' in user request), do not perform the update.
- Ensure the logic is atomic and idempotent for the current day.

### 2. Cross-Module Consistency
- The `AIRecommendationService` is the single source of truth for recommendations.
- All modules (Dashboard, Messaging, AI Agent) must use the same methods:
    - `get_ai_recommendations`
    - `get_sendable_recommendations`
    - `set_recommendation_mode` / `get_recommendation_mode`

### 3. Messaging UI Refinement
- In `send_message.html`:
    - Clicking individual mode buttons (Hot Deals, etc.) in the modal should only update the selection state, NOT trigger a loading state.
    - The "Show Recommendations" button click should trigger the "Processing..." state.
    - Ensure the "AI View On" state shows "Processing..." if a fetch is required.

## Proposed Changes

### Backend: `ai_agent/backend/recommendations.py`
- Update `refresh_opportunity_temperatures` to include the date and author check.
- Ensure `updated_by` is consistently set to 'AI Recommend'.

### Frontend: `web/message/frontend/templates/send_message.html`
- Modify `selectAiRecommendMode` to be purely synchronous UI update.
- Modify `applyAiRecommendMode` to handle the "Processing..." state on the modal button.
- Ensure `toggleAiRecommend` handles the "Processing..." state on the main button.

## Verification Plan
### Unit Testing
- Add a test case to verify that `refresh_opportunity_temperatures` skips updates if already refreshed by 'AI Recommend' today.
- Verify recommendation results for different modes.

### Manual Verification
- Check Home tab AI Recommend button.
- Check AI Agent chat 'AI Recommend' query.
- Check Send Message tab "Choose AI Recommend Mode" modal behavior.
