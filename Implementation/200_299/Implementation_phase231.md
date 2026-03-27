# Phase 231 Implementation

## Summary

Normalized chat-native create/edit UX for `lead`, `contact`, and `opportunity` in the AI-agent frontend.

## High-Level Changes

- Added auto-scroll for schema-based chat form cards when they are first rendered.
- Added auto-scroll for schema-based validation refresh when the form card is replaced in place.
- Routed `contact` and `opportunity` selection/table Edit actions through the chat-native `OPEN_FORM` flow, matching `lead`.
- Kept the workspace `OPEN_FORM` behavior as fallback only.

## Scope Notes

- Frontend-only phase.
- No change to `OPEN_RECORD` post-submit behavior.
- No object expansion beyond `lead`, `contact`, and `opportunity`.

## Backup

- `backups/200_299/phase231`
