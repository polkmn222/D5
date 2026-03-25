# Task - Phase 164: AI Agent CRUD and UI/UX Enhancements

## CRUD Flow & Feedback
- [x] Extend snapshot card (`_build_chat_card`) to support all core objects (Contact, Opportunity, Product, Asset, Brand, Model, MessageTemplate).
- [x] Ensure successful `CREATE` and `UPDATE` return this snapshot card for all objects.
- [x] Verify `Edit` and `Delete` buttons are in the snapshot card header.
- [x] Verify immediate row removal from all visible tables upon record deletion.

## Data Table UI
- [x] Refine control bar layout: `[Select All] [Clear All] [Open] [Edit] [Delete]` buttons.
- [x] Ensure instruction "Select records to take action." is at the top.
- [x] Ensure "Selected: ? items" is below the buttons.
- [x] Ensure selection footer `#ai-agent-selection-bar` is hidden.

## Intelligent Selection
- [x] Add localized multi-select guidance for `Open` and `Edit`.
- [x] Ensure consistent chat-based delete confirmation.

## UX
- [x] Refine auto-scroll logic for tables and forms.
