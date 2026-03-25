# Phase 74 Task

## Context

Legacy AI agent backup files were still stored under `.gemini/development/ai_agent/backups/` instead of the centralized backup tree.

## Goals

- Move all AI agent backup files into `.gemini/development/backups/phaseN/`.
- Preserve phase numbers and restore phase-relative paths under `ai_agent/backend/` and `ai_agent/frontend/`.
- Remove the now-empty legacy AI agent backup directory.
