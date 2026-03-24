# Task: Phase 46 - AI Agent UI Customization & Dashboard Restoration

## Objective
Restore the "AI Recommend" functionality on the Home tab and empower the AI Agent to dynamically modify UI elements (specifically table formats) via natural language. Additionally, redesign the AI Agent's input area to improve usability for long queries.

## Sub-tasks
1. **Dashboard Restoration**:
   - Verify and fix the target containers for `startAiRecommend` in `ai_agent.js`.
   - Ensure the "Start Recommend" button correctly triggers the dashboard update.
2. **AI-Driven UI Modification**:
   - Add a `MODIFY_UI` intent to `AiAgentService`.
   - Implement frontend logic to handle table styling changes (Compact vs. Modern Grid).
   - Add a "🎨 Change Table Format" button to the Quick Guide.
3. **AI Agent UX Improvements**:
   - Expand the chat footer in `ai_agent.css` to provide a larger, more modern input area.
   - Increase font sizes and padding in the input wrapper for a premium feel.
4. **Validation**:
   - Confirm "AI 추천해줘" and "테이블 형식 바꿔줘" both work as expected.
   - Verify the dashboard recommendation table appears correctly.

## Completion Criteria
- Dashboard "Start Recommend" button is functional.
- AI Agent can change its own result table format on command.
- The input bar is significantly more spacious and comfortable to use.
- Phase 46 documentation is generated.