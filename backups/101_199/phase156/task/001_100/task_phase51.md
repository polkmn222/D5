# Phase 51 Task

## Scope
- Prevent unsafe direct create execution from short natural-language prompts.
- Keep short-lived chat context for the current AI Agent conversation.
- Ask clarification questions when the user mentions multiple objects or actions.

## Acceptance Criteria
- `create lead` responds with a field request, not immediate create execution.
- `create lead last name Kim status New` can still proceed through execution flow.
- Same `conversation_id` allows follow-up references like `show the lead I just created`.
- Different `conversation_id` values do not share context.
- Multi-object requests produce clarification responses.
- Multi-action requests produce clarification responses.
- Unit tests pass.
