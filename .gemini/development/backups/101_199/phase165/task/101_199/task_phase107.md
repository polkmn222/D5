# Phase 107 Task

## Context

- Modal-based create and update flows needed to support `Save & New` in the shared AJAX submit path.
- The UI also needed a visible loading state for normal user actions like tab navigation, create, edit, delete, bulk delete, and other CRUD interactions, while excluding AI agent controls.

## Goals

- Add `Save & New` to the shared AJAX modal flow.
- Show a consistent loading indicator during user-driven navigation and CRUD actions.
- Exclude AI recommendation and agent controls from the loading overlay behavior.
