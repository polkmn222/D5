# Workflow

## Phase Numbering Rule

Before creating any new phase artifacts, find the next unused phase number across all of these locations:

- `task/<range>/task_phaseN.md`
- `Implementation/<range>/Implementation_phaseN.md`
- `Walkthrough/<range>/Walkthrough_phaseN.md`
- `.gemini/development/backups/<range>/phaseN/`

Never overwrite an existing phase number. If one folder already contains `phase65`, use the next fully unused phase number instead.

## Phase Execution Sequence

### 1. Planning

- Create `task/<range>/task_phaseN.md` with the scope, constraints, and success criteria.
- Review `agent.md`, `skill.md`, `architecture.md`, and `deployment.md` before making structural changes.
- Review all active markdown files under `.gemini/development/docs/` before making project changes that affect behavior, architecture, workflow, deployment, or standards.
- Use this review priority when the docs set is large: `docs/*.md` -> `docs/testing/*.md` -> D4-specific skill guides -> imported agency skill docs.
- When working on tests, also review the canonical testing docs under `.gemini/development/docs/testing/`.
- Before planning or running unit tests, read the canonical testing docs under `.gemini/development/docs/testing/`.
- Identify which files will need backup copies under `.gemini/development/backups/<range>/phaseN/`.
- Create new project-level markdown files in `.gemini/development/docs/` unless they are phase tracking artifacts in `task/`, `Implementation/`, or `Walkthrough/`, or a folder-local README.

### 2. Backup

- Copy every file that will be edited or deleted into `.gemini/development/backups/<range>/phaseN/` before changing it.
- Always create the grouped range folder first when needed, then create the dedicated phase folder inside it. Do not place loose phase folders directly under `.gemini/development/backups/`.
- Preserve relative structure when practical, especially for docs, backend files, frontend files, and AI agent files.
- If code changes are made, store the pre-change versions in the phase backup folder as well.
- If the phase is docs-only, still back up each edited active doc and note explicitly that no runtime code changed.
- Use hundred-style grouped ranges: `001_100` for phases 1-100, `101_199` for phases 101-199, `200_299` for phases 200-299, and continue the same pattern for later ranges.

### 3. Execution

- Make changes in small, reviewable units.
- Keep documentation synchronized with runtime changes in the same phase.
- Use the same phase number for `task`, `Implementation`, `Walkthrough`, and `backups` artifacts.
- Do not reorganize the established top-level folder structure unless the user explicitly asks for a structural migration.
- Keep pytest cache output consolidated at `.gemini/development/.pytest_cache` only.
- If Antigravity MCP `sequential-thinking` is available in the current toolchain, use it for structured planning; if it is not available, continue by following the docs-driven workflow without blocking the implementation.

### 4. Verification

- Run focused validation for the surfaces that changed.
- Record what was verified, what was not run, and why.
- Check that deployment docs still match `vercel.json`, `render.yaml`, and the active entry points.
- If a secondary `.pytest_cache` appears at the repository root, under `.gemini/`, or in another subdirectory, treat it as accidental local state and merge it back into `.gemini/development/.pytest_cache`.
- When known test failures or skips are documentation-related rather than confirmed runtime regressions, record them in the active testing docs instead of silently normalizing them away.

### 5. Completion

- Create `Implementation/<range>/Implementation_phaseN.md` describing the changes.
- Create `Walkthrough/<range>/Walkthrough_phaseN.md` summarizing the final state and validation.
- Report the chosen phase number so concurrent work can be traced cleanly.
- Keep backup outputs grouped under `.gemini/development/backups/<range>/phaseN/` so each phase can be reviewed independently.
