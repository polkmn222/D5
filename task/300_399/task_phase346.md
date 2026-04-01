# Phase 346 Task

## Request

Show message sending as fully blocked on Render with an administrator-contact label, including AI Agent.

## Scope

- Update the Send Message UI to present the blocked state with explicit administrator-contact copy.
- Update the AI Agent UI to disable Send Message entry points and show the same blocked-state guidance.
- Add focused unit coverage for the changed UI behavior.

## Constraints

- Do not expand scope beyond the blocked-state UI presentation.
- Use unit tests only.
- Do not use manual testing.

## Success Criteria

- Render blocked-state messaging surfaces show administrator-contact guidance before send.
- AI Agent Send Message entry points are visibly blocked on Render.
- Focused unit tests pass.
