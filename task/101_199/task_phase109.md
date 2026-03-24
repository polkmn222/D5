# Phase 109 Task

## Context

The Home sidebar AI Recommend card should let users manually change the shared recommendation logic without going through the AI Agent chat. The control needs to update both Home and Send Message because they now share the same sendable recommendation source.

## Goals

- Add manual recommendation mode buttons to the Home sidebar AI Recommend card.
- Wire the buttons to update the shared recommendation mode and refresh the Home recommendation fragment.
- Add unit coverage for the new dashboard controls and mode-change endpoint.
