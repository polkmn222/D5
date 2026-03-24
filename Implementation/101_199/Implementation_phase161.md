# Implementation Plan - Phase 161: Search Fix, Trash UX, and Comprehensive Testing

## Goal
Fix the broken list view search filtering, enhance the Recycle Bin with detailed confirmation dialogs, and execute a full suite of unit tests to ensure system stability.

## Key Changes

### 1. List View Search Engine Fix
- **File**: `web/frontend/static/js/list_views.js`
- **Fix**: Update `applyRowWindowing` to explicitly hide (`display: none`) rows where `data-filter-visible="false"`. Currently, it only toggles visibility for the "true" subset, leaving stale rows visible.

### 2. Recycle Bin UX Enhancement
- **File**: `web/frontend/templates/trash/list_view.html`
- **Restore Confirmation**: Implement `confirmRestore(objType, id, name)` to prevent accidental restores.
- **Detailed Messaging**: Update both Restore and Permanent Delete modals to show the Object Type and Record Name (e.g., "Are you sure you want to restore Contact 'Jiho Park'?").

### 3. Comprehensive Unit Testing
- **Execution**: Run all existing 21 unit tests.
- **New Tests**:
    - `test_lookup_sync.py`: Verify automatic Brand/Model mapping when a Product is selected.
    - `test_search_logic`: Verify that the filtering logic correctly identifies matches.
    - `test_trash_cascading`: Verify that permanent deletion handles foreign keys correctly (from Phase 159).

## Verification
- **Manual**: Test "Search this list" in Contacts/Leads. Test Restore/Delete in Trash with new modals.
- **Automated**: Achieve 100% pass rate on all CRM unit tests.

## Documentation & Backups
- Backup modified files to `.gemini/development/backups/101_199/phase161/`.
