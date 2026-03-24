# Phase 76 Task

## Context

The test reorganization plan from Phase 75 needed to be applied to the actual unit test tree, the unit-test workflow needed a stronger `docs/testing` requirement, and pytest cache policy needed to move back under `.gemini/development`.

## Goals

- Make `docs/testing` a mandatory review step for unit test work.
- Move the current unit tests into the target domain-oriented folder structure.
- Consolidate pytest cache into `.gemini/development/.pytest_cache`.
- Assess portability of local skill folders for ChatGPT and OpenAI usage.
