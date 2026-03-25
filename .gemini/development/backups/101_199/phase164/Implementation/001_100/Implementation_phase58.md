# Phase 58 - Duplicate Review Controls and Preview/Send Parity

## Goals
- Let users choose duplicate recipients at the per-record level.
- Make preview and final send use the same delivery plan.
- Improve trust in the Send Message flow.

## Implemented Changes

### 1. Per-Record Duplicate Review
- Added checkbox controls inside each duplicate phone group.
- Users can:
  - keep one recipient per phone,
  - select all duplicates,
  - manually choose exactly which duplicate records should be included.

### 2. Preview/Send Parity
- Added shared helpers for:
  - current message config,
  - recipient plan resolution,
  - grouped send payload generation.
- Preview now reflects the same filtered recipient set that the send action will use.
- Preview explains when duplicate recipients are excluded.
- Sending from preview now uses the exact same resolved delivery plan.

## Files Changed
- `.gemini/development/frontend/templates/send_message.html`

## Backup
- `.gemini/development/backups/phase58/`
