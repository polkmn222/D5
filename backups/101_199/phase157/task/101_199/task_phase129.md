# Phase 129 Task

## Context

AI Recommend mode rules need one more alignment pass: `Hot Deals`, `Closed Won`, and `New Records` should all use a 7-day window, while `Follow Up` should remain driven only by followed opportunities.

## Goals

- Keep `Hot Deals` on recent 7-day Test Drive opportunities.
- Keep `Closed Won` on recent 7-day won opportunities.
- Restrict `New Records` to recent 7-day non-won/non-lost opportunities.
- Keep `Follow Up` limited to `is_followed = true` open opportunities.
