# Implementation Plan - Phase 160: Recycle Bin Infinite Scroll and Enhanced Search

## Goal
Implement infinite scrolling (windowing) for the Recycle Bin to improve performance by loading 50 records at a time, and ensure the search functionality works seamlessly with this new loading logic.

## Key Changes

### 1. Frontend: Infinite Scroll & Search Integration
- **Template**: Update `web/frontend/templates/trash/list_view.html`.
- **State Management**:
    - `displayLimit`: Initialized to 50.
    - `searchTerm`: Tracks current search input.
- **New Logic**:
    - `applyTrashFiltersAndWindowing()`:
        1. Filters all `.trash-row` elements based on `searchTerm`.
        2. Within the filtered set, shows only the first `displayLimit` rows.
        3. Updates the item count summary.
    - **Scroll Listener**: Monitors the window scroll position. When nearing the bottom, it increases `displayLimit` by 50 and re-applies the windowing logic with a brief loading state.
- **UI Components**:
    - Add a "Loading more..." spinner/indicator below the table.

### 2. UI Consistency
- Maintain the Salesforce Lightning aesthetics.
- Ensure the "Search this list..." input correctly triggers the re-filtering and resets the scroll position if needed.

## Verification
- **Initial Load**: Verify only the first 50 deleted records are visible.
- **Search**: Type a name and verify it filters across all records, not just the visible 50.
- **Scroll**: Scroll down and verify more records appear until the list is exhausted.
- **Empty State**: Ensure appropriate messaging when no records match the search.

## Documentation & Backups
- Record progress in `Implementation/`, `task/`, and `Walkthrough/`.
- Backup modified files to `.gemini/development/backups/101_199/phase160/`.
