# Task - Phase 163: AI Agent Enhancements (CRUD Flow, Table UI, and UX)

## Planning
- [x] Analyze existing AI Agent frontend code (`ai_agent.js`, `ai_agent.css`, `ai_agent_panel.html`)
- [/] Create Implementation Plan and get User Confirmation
- [ ] Research existing tests and plan new automated tests

## Execution - Step 1: Backups and Foundation
- [ ] Backup all modified files to `.gemini/development/backups/101_199/phase163/`
- [ ] Fix any minor structural issues in `ai_agent_panel.html` (e.g., IDs, containers)

## Execution - Step 2: CRUD Flow & Snapshot Improvements
- [ ] Modify `wireAgentInlineForm` to trigger a "Show [object] [id]" query after successful save
- [ ] Update `renderAgentChatCard` to include `Edit` and `Delete` buttons in the header
- [ ] Implement `triggerSnapshotEdit` and `triggerSnapshotDelete` logic

## Execution - Step 3: Data Table UI Enhancements
- [ ] Relocate control bar to the top of the table in `renderAgentResultsMarkup`
- [ ] Add "Search in table..." input field and implement `filterAgentTable` logic
- [ ] Update selection status display ("Selected: ? items") below the button bar
- [ ] Hide the old "Selection Ready" footer bar

## Execution - Step 4: Intelligent Interaction & Deletion logic
- [ ] Update `triggerSelectionOpen` and `triggerSelectionEdit` to show chat-based guidance for multiple selections
- [ ] Implement chat-based delete confirmation with `[Yes]` and `[Cancel]` buttons
- [ ] Implement `removeAgentTableRow` to immediately reflect deletions in all visible tables

## Execution - Step 5: UX Polishing
- [ ] Add auto-scroll logic to tables and forms in `appendChatMessage` and `appendAgentInlineFormMessage`

## Verification
- [ ] Run `pytest` for AI Agent CRUD logic
- [ ] Create a new unit test for table filtering logic
- [ ] (Simulated) Verify UI changes (Selection bar relocation, Search input, Snapshot buttons)
- [ ] Verify auto-scroll behavior

## Finalization
- [ ] Create `Walkthrough_phase163.md`
