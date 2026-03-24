# Phase 146 Task

## Context

- The user wants lead CRU inside AI Agent to feel more like a pasted chat artifact than a separate interactive workspace.
- Existing screenshots show the lead create modal, detail page, and edit modal that should inform the chat presentation.
- All active docs under `.gemini/development/docs/` were reviewed before planning this phase.

## Goals

- Shift lead open/edit/create feedback toward a chat-embedded pasted snapshot pattern.
- Keep the existing selection bar and broader AI Agent behavior intact for non-lead flows.
- Fix any AI Agent panel markup mismatch uncovered while implementing the pasted-chat pattern.
- Store phase 146 artifacts and backups using the documented workflow.

## Success Criteria

- Lead create, open, and edit flows can surface a compact pasted-style card in chat.
- Lead selection actions prefer the chat snapshot experience over the workspace fetch path.
- Other object flows do not regress, and messaging workspace behavior remains available.
- Phase 146 task, implementation, walkthrough, and backups are created consistently.
