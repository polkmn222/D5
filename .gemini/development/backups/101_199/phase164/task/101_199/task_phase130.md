# Phase 130 Task

## Context

`Closed Won` AI recommendations are still surfacing older deals because some opportunities carry future-facing `close_date` values that should not be treated as the actual recent win signal.

## Goals

- Tighten `Closed Won` recommendation filtering so only genuinely recent wins appear.
- Add regression coverage for future `close_date` values on older won opportunities.
