# Phase 118 Task

## Context

The AI Agent table should show object-specific fields only, record clicks should become selection-first with explicit actions, multi-select delete should work, and Hot Deals / Closed Won recommendations must respect the new 7-day window rule.

## Goals

- Add object-specific result-table schemas for the AI Agent.
- Change row clicks to selection-first and expose `Open`, `Edit`, `Delete`, and `Send Message` actions.
- Support deleting multiple selected records from the AI Agent.
- Limit `Hot Deals` and `Closed Won` recommendations to the most recent 7 days.
