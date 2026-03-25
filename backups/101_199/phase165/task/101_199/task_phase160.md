# Task - Phase 160: Recycle Bin Infinite Scroll and Enhanced Search

## Tasks

### 1. State and Filter Logic
- [ ] Initialize `trashState` in `list_view.html` with `displayLimit: 50` and `searchTerm: ''`.
- [ ] Implement `applyTrashFiltersAndWindowing()` to handle combined searching and scrolling logic.

### 2. Scroll Interaction
- [ ] Add a global `scroll` event listener to detect when the user hits the bottom of the list.
- [ ] Implement a simulated loading delay (300ms) for smoother UX.

### 3. UI Updates
- [ ] Add a loader container below the trash table.
- [ ] Update the summary text (e.g., "Showing 50 of 120 items") to reflect the current state.
- [ ] Update the search input `oninput` handler to use the new logic.

### 4. Verification
- [ ] Verify infinite scroll triggers correctly at the bottom.
- [ ] Verify search resets the display limit or appropriately shows filtered results.
- [ ] Check for console errors or layout breaks.

### 5. Finalize
- [ ] Create `Walkthrough_phase160.md`.
- [ ] Backup all changes to `.gemini/development/backups/101_199/phase160/`.
