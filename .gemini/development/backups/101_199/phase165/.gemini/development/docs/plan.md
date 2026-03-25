# Documentation and Maintenance Plan

## Purpose

This plan defines how the active documentation set should evolve with the codebase.

## Current Priorities

### 1. Runtime Accuracy

- Keep all high-level documents aligned with the active FastAPI entry points.
- Treat PostgreSQL as the current database baseline.
- Keep the mounted AI agent and shared template paths documented.

### 2. Deployment Clarity

- Document the Vercel adapter path through `api/index.py`.
- Document the Render service rooted at `.gemini/development`.
- Keep required environment variables centralized in deployment guidance.

### 3. Surface-Specific Guidance

- Keep `skill.md` focused on backend, frontend, and AI agent implementation concerns.
- Keep `ui_standards.md` focused on UI rules rather than system architecture.
- Keep `erd.md` focused on active models rather than historical schemas.

### 4. Phase Traceability

- Record each meaningful documentation or code change in `task/<range>/`, `Implementation/<range>/`, and `Walkthrough/<range>/` using the next unused phase number.
- Preserve a full pre-change codebase snapshot in the grouped backup path, for example `.gemini/development/backups/101_199/phaseN/`.
- Avoid overwriting an existing phase number even if the numbers are non-contiguous.
