# Phase 135 Task

## Context

- The user requested documentation-first reinforcement based on the current implemented D4 codebase, with no runtime code changes.
- The active D4 docs live under `.gemini/development/docs/`, and the testing source of truth lives under `.gemini/development/docs/testing/`.
- Imported skill libraries also exist under `.gemini/development/docs/skills/agency-agents/`, but they need D4-specific usage guidance so they do not override canonical project docs.

## Goals

- Update core canonical docs to match the current runtime structure and current messaging/UI behavior.
- Update testing docs to reflect the current command set, known failures, known skips, and migration cautions.
- Add D4-specific guidance for imported skill markdown so it is treated as supplemental reference material.
- Keep this phase documentation-only and avoid runtime code changes.
