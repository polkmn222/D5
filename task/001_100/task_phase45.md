# Task: Phase 45 - Dashboard & AI Agent Feature Integration

## Objective
Enable seamless transition of key dashboard functionalities (AI Recommendations, Messaging, Top Deals) into the AI Agent. Fix non-functional dashboard buttons and expand the AI Agent's Quick Guide and intent execution logic to handle these specialized CRM tasks.

## Sub-tasks
1. **Restore Dashboard Functionality**:
   - Fix the broken "Start Recommend" button on the Home tab by restoring the `startAiRecommend` JavaScript function in `ai_agent.js`.
2. **AI Agent Backend Enhancement**:
   - Update `AiAgentService` to support a new `RECOMMEND` intent.
   - Integrate `AIRecommendationService` into the agent's intent executor.
   - Add keyword overrides for "AI Recommend" and "Send Message" to ensure predictable behavior.
3. **AI Agent Frontend Expansion**:
   - Add "✨ AI Recommend", "✉️ Send Message", and "🏆 Show top deals" to the Quick Guide sidebar in `ai_agent.html`.
4. **Validation**:
   - Confirm the "Start Recommend" button on the Home tab correctly populates the recommendations fragment.
   - Verify that clicking "AI Recommend" in the AI Agent window returns a sortable table of recommended opportunities.
   - Ensure the AI Agent provides helpful guidance when asked about sending messages.

## Completion Criteria
- Dashboard "AI Recommend" button is functional.
- AI Agent can directly provide AI-driven recommendations in its chat window.
- Quick Guide includes new specialized commands.
- Phase 45 documentation and backups are generated.