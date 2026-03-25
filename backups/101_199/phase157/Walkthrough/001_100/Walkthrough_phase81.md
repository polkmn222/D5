# Walkthrough - Phase 81

## What Changed
The messaging feature is no longer scattered across the general web backend and frontend folders.

## New Structure
- Shared CRM runtime remains under `web/backend/` and `web/frontend/`.
- Messaging now has its own dedicated subsystem under `web/message/`.

## Why This Helps
- Message sending, template management, provider dispatch, and send-specific templates are easier to reason about in one place.
- The general CRM runtime no longer needs to own all messaging-specific implementation files directly.

## Validation
- Focused messaging and UI tests passed.
- Full unit suite passed with `205 passed, 4 skipped`.
