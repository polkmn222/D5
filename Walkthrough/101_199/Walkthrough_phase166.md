# Walkthrough - Phase 166: AI Agent Project Directives Consolidation

## Overview
This phase successfully established a formal, mandatory set of operating directives for the AI Agent (Antigravity). Instead of creating a separate `project_rules.md`, these directives were consolidated into the existing `.gemini/development/docs/workflow.md` to serve as a single, unified source of truth for the project's workflow.

## Changes Implemented

### 1. Updates to Backup Workflow
- Modified the backup rule in `workflow.md` to deprecate the "full codebase backup" approach.
- The AI is now instructed to perform **targeted, module-specific backups**, saving ONLY the modified code modules into `.gemini/development/backups/<range>/phaseN/`.
- Re-emphasized that `.md` files must never be deleted, even during backup operations.

### 2. Integration of AI Agent Operational Directives
Added a new dedicated section `## AI Agent Operational Directives` to `workflow.md` outlining these strict rules:
- **English-Only Markdown**: Mandating that all `.md` files are written exclusively in English.
- **Focused Context Reading**: The AI is forbidden from needlessly scanning historical/tracking folders (`implementation`, `task`, `walkthrough`, `backups`) and must only read folders related to the active task.
- **Strict Testing Policy**: Enforcing unit tests while strictly forbidding all manual testing.
- **Error/Doubt Protocol**: Requiring the AI to notify the user before fixing errors or making architectural decisions.
- **Execution Confirmation**: Mandating user approval before file modification execution begins.
- **Tool Constraints**: The AI must consistently use the `sequential-thinking` MCP tool.

## Validation Results
- Verified that the `workflow.md` now cleanly presents the new rules without overwriting other established architectural constraints.
- Verified that all planning/task documentation (`Implementation_phase166.md` and `task_phase166.md`) was rewritten strictly in English to comply with the new Language Policy.

The project is now fully governed by these consolidated constraints.
