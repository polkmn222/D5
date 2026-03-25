# Implementation Plan - Phase 166: AI Agent Project Directives Consolidation

## Objective
Update the existing `.gemini/development/docs/workflow.md` document to integrate a mandatory set of rules for the AI Agent. This approach resolves the conflict between the old "full codebase backup" rule and the newly established "partial module backup" rule, and centralizes all development procedures into a single source of truth.

## Proposed Changes

### Documentation (Target: `.gemini/development/docs/workflow.md`)
- **[MODIFY] workflow.md**: We will revise the existing workflow document to embed the following 11 absolute rules the AI must abide by. We will replace the old full-backup directive with the new module-specific backup directive.

#### New AI Agent Directives to be Added/Updated:
1. **Markdown Integrity:** Never delete `.md` files (this applies strictly to backup scenarios as well).
2. **Folder Structure:** Never alter the original folder naming conventions or structure during backups.
3. **Phase Tracking for Documents:** When storing documentation in the `implementation`, `task`, or `walkthrough` folders, the current `phase` indicator must be appended (e.g., `Implementation_phase166.md`).
4. **Targeted Code Backups (OVERRIDING OLD RULE):** If code modules are modified, back up strictly the *modified module (folder)* into the `backups` directory, appending the current `phase` to the folder name, instead of copying the entire repository.
5. **Strict Testing Policy:** Unit tests are absolutely mandatory. Manual testing is strictly forbidden.
6. **Focused Context Reading:** During development, the AI must NOT indiscriminately scan or read all folders. It should only read the specific folders directly related to the current development task. History folders (`implementation`, `task`, `walkthrough`, `backup`) are to be ignored by default.
7. **Error/Doubt Protocol:** If an error occurs, or if there is doubt regarding a piece of code, or if structural changes seem necessary, the AI must NOT modify the code immediately. It must notify and seek guidance from the user first.
8. **Tool Usage:** The AI Agent (Antigravity) must actively utilize the MCP Tool `sequential-thinking` throughout its execution.
9. **Execution Confirmation:** The AI must unconditionally request user confirmation before starting the execution of any actual file modifications.
10. **Planning First:** Every major step must begin with writing a detailed implementation plan (e.g., `Implementation_phaseXXX.md` in the project directory) and must gain user approval before proceeding.
11. **English-Only Markdown:** ALL Markdown (`.md`) files must be written entirely in English, unconditionally.

### AI Tool Workflow
The AI will execute this plan to append/modify `.gemini/development/docs/workflow.md`. Once complete, it will generate `Walkthrough/101_199/Walkthrough_phase166.md`. 

## Verification Plan
1. Receive user review and explicit authorization for this consolidated plan.
2. Carefully edit `workflow.md` ensuring no previously valid steps are destroyed, only superseded where there is conflict (e.g., the backup rule).
