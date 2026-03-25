# Phase 71 Task

## Context

The backup policy needed to explicitly require phase-specific backup folders.

## Goals

- Document that backups must always be stored inside `.gemini/development/backups/phaseN/`.
- Prevent loose backup files from being written directly under `.gemini/development/backups/`.
