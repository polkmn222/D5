# Task: Phase 31 - AI Agent UI Revamp & Transparency

## Objective
Redesign the AI Agent's user interface to match a high-fidelity benchmark (Salesforce-aligned aesthetics). Key focus areas include distinct message bubbles for users and the agent, transparent reasoning (showing how the agent understood the query), and visible SQL query blocks.

## Sub-tasks
1. **CSS Revamp**:
   - Create a modern, clean look with rounded corners (16px) and subtle shadows.
   - Implement distinct styles for `.msg-user` (reddish icon) and `.msg-agent` (orange icon).
   - Style the `.sql-block` with a monospace font and structured background.
   - Improve table styling for results, including hover effects and consistent padding.
2. **JavaScript Updates**:
   - Refactor `appendChatMessage` to render the new bubble structure.
   - Inject the generated SQL into the agent's response bubble for transparency.
   - Add "Select All" and "Clear All" functionality to result tables.
   - Improve the input area with a modern rounded bar and SVG send button.
3. **Template Polish**:
   - Update `ai_agent.html` to align with the new sidebar and header structure.
   - Use clean SVGs for icons and buttons.
4. **Validation**:
   - Manually verify the layout across all states (normal, minimized, maximized).
   - Ensure SQL blocks are only shown when a database query is actually performed.

## Completion Criteria
- UI matches the provided benchmark screenshot.
- User and Agent messages are visually distinct.
- SQL queries are visible and well-formatted.
- Tables include interactive controls (Select/Clear All).
- Phase 31 documentation is generated.