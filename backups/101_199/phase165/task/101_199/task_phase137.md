# Phase 137 Task

## Context

- The user requested a manual-test pass limited to non-messaging-send and non-AI-agent areas.
- The user also requested that manual-test records be stored under the `test/manual/` area in an organized way.
- This phase should not modify runtime code; it should perform local validation and preserve the results.

## Goals

- Run a local HTTP-based manual validation pass for dashboard and core CRM routes.
- Exclude `Send Message` flows and all AI Agent flows.
- Save the manual-test evidence under `.gemini/development/test/manual/evidence/`.
- Report any suspicious or unclear findings without changing code.
