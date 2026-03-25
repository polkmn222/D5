# Phase 122 Task

## Context

The Home tab is doing too much work up front. AI recommendations should load only when `Start Recommend` is clicked, and the AI Agent panel should load only when `Ask AI Agent` is clicked.

## Goals

- Remove eager AI recommendation fetching from the Home dashboard load.
- Keep AI Recommend loading on demand through `/api/recommendations` only.
- Lazy-load the AI Agent panel markup on demand instead of rendering it during initial Home load.
