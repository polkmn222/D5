# Phase 153 Task

## Context

- The AI Agent runtime has grown into a few large backend and frontend files, which makes parallel work across terminals harder and increases regression risk.
- The requested direction is a feature-first layout, but still clearly separated under `backend/` and `frontend/`.
- The refactor should begin safely with bridge modules and structure ownership so existing imports and runtime behavior stay intact.

## Goals

- Introduce a backend/frontend feature layout for AI Agent without breaking current entrypoints.
- Move stable modules into feature folders first and leave compatibility shims at the legacy import paths.
- Create explicit backend feature areas for `llm`, `recommend`, `messaging`, and `objects`, with object-specific folders.
- Create matching frontend feature areas so future UI work can split by shell, lead object flows, recommend, and messaging.

## Success Criteria

- Existing runtime imports still work.
- New backend feature modules exist for shell, llm, and recommend responsibilities.
- New frontend feature folders exist for shell, lead, recommend, and messaging responsibilities.
- Unit tests cover the compatibility bridges and the new structural contract.
