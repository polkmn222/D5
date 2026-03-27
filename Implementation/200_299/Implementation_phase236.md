# Phase 236 Implementation

## Summary
- Added chat-native opportunity lookup parity for `brand` only.
- Reused the existing generic chat-native lookup control pattern.
- Kept the scope to the narrow safe lookup slice: search, select, preload, clear, and submit ID.

## High-Level Changes
- Updated the opportunity chat-native form schema to expose `brand` as a lookup field.
- Added opportunity edit-form preload support for the selected brand display label.
- Added focused unit coverage proving that the selected brand ID is submitted unchanged.

## Changed Modules
- `development/ai_agent/ui/backend`
- `development/test/unit/ai_agent/backend`

## Backup
- `backups/200_299/phase236/`
