# Phase 343 Task

## Request

Fix the false "Message service is unavailable" banner for the Render self-relay deployment path.

## Scope

- Adjust the messaging demo availability check only for self-relay runtime behavior.
- Update focused unit tests for the corrected availability path.

## Constraints

- Do not expand scope beyond the self-relay availability false negative.
- Use unit tests only.
- Do not use manual testing.

## Success Criteria

- Render self-relay deployments do not fail availability checks only because they probe their own public relay endpoint.
- Focused messaging unit tests pass.
