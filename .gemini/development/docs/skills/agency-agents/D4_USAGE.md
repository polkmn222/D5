# D4 Usage Guide For Imported Agency Skills

## Purpose

This file explains how D4 should use the imported `agency-agents` markdown library without letting that external material override project-specific rules.

## Priority Rules

- D4 runtime docs under `docs/*.md` always win.
- D4 testing docs under `docs/testing/*.md` always win for validation and test execution.
- Actual implemented code wins over generic external playbooks when the D4 docs have not caught up yet.
- Imported `agency-agents` docs are supplemental references for planning style, decomposition, prompts, and role framing.

## Safe Usage

- Use imported agency docs to borrow planning patterns, review checklists, and collaboration prompts.
- Use them when you want role-specific thinking such as reviewer, devops, or architect framing.
- Keep any adopted rule D4-specific by rewriting it into canonical D4 docs before treating it as project policy.

## Do Not Do

- Do not treat imported agency docs as D4 product requirements.
- Do not change runtime behavior just because an imported skill doc recommends a different workflow.
- Do not assume imported naming, paths, or testing conventions match the D4 repository.
- Do not edit generated third-party reference files such as `CONVENTIONS.md` just to add D4 rules; add D4 wrapper docs like this one instead.

## Recommended Reading Order

1. `docs/agent.md`
2. `docs/workflow.md`
3. `docs/skill.md`
4. `docs/testing/README.md` when testing is involved
5. `docs/skills/agency-agents/D4_USAGE.md`
6. Imported `docs/skills/agency-agents/**` references as needed
