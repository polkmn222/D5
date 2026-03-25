# Workflow

## Phase Numbering Rule

Before creating any new phase artifacts, find the next unused phase number across all of these locations:

- `task/<range>/task_phaseN.md`
- `Implementation/<range>/Implementation_phaseN.md`
- `Walkthrough/<range>/Walkthrough_phaseN.md`
- `backups/<range>/phaseN/`

Never overwrite an existing phase number. If one folder already contains `phase65`, use the next fully unused phase number instead.

**Historical File Immutability**: All files related to completed or ongoing phases (`task_phaseN.md`, `Implementation_phaseN.md`, `Walkthrough_phaseN.md`, and `backups/phaseN/`) are strictly immutable. Once a phase number is assigned and used, the corresponding files must NEVER be modified, overwritten, or updated in subsequent phases. Always move to the next available phase number for any new or follow-up work.

## Phase Execution Sequence

### 1. Planning

- Create `task/<range>/task_phaseN.md` with the scope, constraints, and success criteria.
- Review `agent.md`, `skill.md`, `architecture.md`, and `deployment.md` before making structural changes.
- Review all active markdown files under `.gemini/development/docs/` before making project changes that affect behavior, architecture, workflow, deployment, or standards.
- Use this review priority when the docs set is large: `docs/*.md` -> `docs/testing/*.md` -> D4-specific skill guides -> imported agency skill docs.
- When working on tests, also review the canonical testing docs under `.gemini/development/docs/testing/`.
- Before planning or running unit tests, read the canonical testing docs under `.gemini/development/docs/testing/`.
- All repository files will be backed up as a full codebase snapshot under `backups/<range>/phaseN/`.
- Create new project-level markdown files in `.gemini/development/docs/` unless they are phase tracking artifacts in `task/`, `Implementation/`, or `Walkthrough/`, or a folder-local README.

### 2. Backup

- Rather than copying every file, back up STRICTLY the modified modules (folders) into `backups/<range>/phaseN/` before starting execution.
- Never delete `.md` files under any circumstances, including during the backup process.
- Always create the grouped range folder first when needed, then create the dedicated phase folder inside it. Do not place loose phase folders directly under `backups/`.
- Preserve the exact relative structure of the entire repository for the modules being backed up.
- This targeted, module-specific backup is mandatory for every phase.
- Use hundred-style grouped ranges: `001_100` for phases 1-100, `101_199` for phases 101-199, `200_299` for phases 200-299, and continue the same pattern for later ranges.

### 3. Execution

- Make changes in small, reviewable units.
- Keep documentation synchronized with runtime changes in the same phase.
- Use the same phase number for `task`, `Implementation`, `Walkthrough`, and `backups` artifacts.
- Do not reorganize the established top-level folder structure unless the user explicitly asks for a structural migration.
- Keep pytest cache output consolidated at `.gemini/development/.pytest_cache` only.
- The AI Agent (Antigravity) MUST unconditionally use the MCP `sequential-thinking` tool for structured planning on every task.

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
- Keep backup outputs grouped under `backups/<range>/phaseN/` so each phase can be reviewed independently.

## AI Agent Operational Directives

In addition to the phase workflows, the AI Agent must rigidly adhere to the following rules:

1. **English-Only Markdown**: ALL markdown (`.md`) files must be written strictly in English, unconditionally.
2. **Focused Context Reading**: The AI must only read folders and files directly related to the active development task. Proactively scanning historical or tracking folders (`implementation`, `task`, `walkthrough`, `backups`) is forbidden unless specifically instructed otherwise.
3. **Strict Testing Policy**: Unit tests are absolutely mandatory for any logic changes. Manual testing is strictly forbidden.
4. **Error/Doubt Protocol**: If an error occurs, if code is questionable, or if architectural changes are deemed necessary, the AI must NOT automatically modify the code. It must notify the user and await explicit guidance.
5. **Execution Confirmation**: The AI must receive explicit user authorization before transitioning from Planning to modifying files in Execution.
6. **Strict Plan Adherence & Confirmation**: The AI MUST present ONLY the current active `Implementation_phaseN.md` plan to the user and receive their EXPLICIT confirmation before modifying any code. It is STRICTLY FORBIDDEN to read past or historical `Implementation`, `task`, or `walkthrough` files, as this introduces outdated context and tangles code logic. Arbitrarily proceeding with development without user authorization of the CURRENT plan is a critical violation.
7. **Phase File Immutability**: The AI Agent is strictly forbidden from modifying, overwriting, or deleting any historical `task`, `Implementation`, or `Walkthrough` files from previous phases. Any NEW development or follow-up work MUST be tracked in a new phase with a higher number.
