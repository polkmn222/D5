# Phase 124 Task

## Context

The AI Agent `Open` and `Edit` actions still rely on an iframe-style workspace, but the desired UX is a true in-chat panel. The Send Message AI Recommend mode picker also needs to be treated as a finished, explicit choice step.

## Goals

- Replace the AI Agent iframe workspace with an injected in-chat detail/edit panel.
- Keep loading feedback while the in-chat workspace fetches content.
- Finalize the Send Message AI Recommend mode selection flow with its explicit chooser state.
