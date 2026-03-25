# Phase 126 Task

## Context

`Error loading opportunities` is caused by the runtime querying `opportunities.updated_by` before the PostgreSQL table has that new column.

## Goals

- Ensure the `opportunities.updated_by` column exists automatically at runtime.
- Remove the resulting transaction-aborted cascade that breaks opportunity and contact pages.
