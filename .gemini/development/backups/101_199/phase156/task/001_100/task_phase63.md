# Phase 63 Task

## Scope
- Keep the AI Agent footer dedicated to the prompt input.
- Move selection actions into the conversation area.
- Ensure AI Agent tables paginate at 50 rows even without server pagination metadata.
- Improve AI Recommend option clarity.
- Show template thumbnails in AI Agent results.
- Add cleanup behavior when template images are replaced.

## Acceptance Criteria
- Footer contains only the prompt input area.
- Selection controls appear inside the chat area.
- AI Agent tables over 50 rows paginate.
- `Change AI Recommend` clearly marks the current option.
- Template image fields render as thumbnails in AI Agent tables.
- Template image replacement cleanup path is covered by tests.
- Regression tests pass.
