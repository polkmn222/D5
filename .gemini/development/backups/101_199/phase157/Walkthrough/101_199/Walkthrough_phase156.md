# Walkthrough - Phase 156: Update Backup Rules

## Summary
The backup policy in the project documentation has been updated to require a **full codebase backup** for every phase change. This ensures that every phase has a complete, runnable snapshot of the entire repository.

## Verification
- Checked `docs/workflow.md`, `docs/plan.md`, `docs/agent.md`, and `docs/skill.md` for the new rule.
- Verified that `.gemini/development/backups/101_199/phase156/` contains a full snapshot of the repository (verified by `rsync` output).
