# Phase 117 Task

## Context

The AI Agent would be easier to control if users could explicitly choose English or Korean from the header, instead of relying only on automatic detection.

## Goals

- Add an `ENG` / `KOR` language toggle to the AI Agent header.
- Send the selected preference with chat requests so the backend can honor it.
- Localize key frontend guidance and the no-selection Send Message prompt to match the chosen language.
