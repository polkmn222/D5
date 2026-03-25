# Phase 48 Task - Improve Lead Intent Recognition

## Goal
Improve natural language robustness for Lead-related commands.

---

## Functional Requirements

1. Detect CREATE intent variations:
   - 리드 만들고 싶어
   - 리드를 만들어줘
   - create lead
   - I want to create laed

2. Detect QUERY intent variations:
   - show all lead
   - all lead
   - 리드 전체

3. Correct common typos:
   - laed → lead
   - leda → lead

4. Maintain strict JSON response format.

5. Use MCP sequential-thinking before final response selection.

---

## Non-Functional Requirements

- No performance degradation > 5%
- No regression in MODIFY_UI / RECOMMEND logic
- Unit tests must pass

---

## Deliverables

- Updated AiAgentService
- Pre-normalization module
- Added unit tests for variation handling
- Phase documentation (Implementation / Task / Walkthrough)
