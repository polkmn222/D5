# Phase 66 Task

## Scope
- Add direct template-to-send action from AI Agent.
- Improve Send Message guidance when a template is handed off from AI Agent.
- Clean up image state when deleting a template.

## Acceptance Criteria
- Template rows expose `Use In Send Message`.
- Send Message shows an import note when the template came from AI Agent.
- MMS handoff specifically highlights that the image preview is ready.
- Template delete triggers image cleanup first.
- Regression tests pass.
