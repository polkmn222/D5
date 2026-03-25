# Phase 112 Task

## Context

The Home AI Recommend card should not auto-load results when a user changes the recommendation mode, and the sidebar should use a single visible toggle control instead of showing all mode buttons at once.

## Goals

- Replace the multi-button mode picker with a single toggle-style control.
- Keep mode changes from auto-loading recommendations; users must press `Start Recommend` to fetch results.
- Add unit coverage for the single-toggle UI and no-auto-load behavior.
