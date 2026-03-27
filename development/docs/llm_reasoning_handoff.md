# LLM Reasoning Handoff

## Purpose And Scope

This note is a short operational handoff for the current `development/ai_agent` reasoning layer.

Use it when continuing work on the fallback LLM reasoning path. It is not a full architecture document. It summarizes the current safe model, the most important assets, and the main boundaries that should not be crossed casually.

## Current Reasoning-Layer State

The current reasoning layer is stronger and more stable than the original fallback path.

What was strengthened:

- structured fallback reasoning contract in `intent_reasoner.py`
- Python-side normalization and validation before execution
- clarification-priority over risky execution
- explicit confidence-band handling
- stronger refusal behavior for unsafe or conflicting outputs
- conservative noisy-English normalization within the current safe scope
- clearer prompt guidance for structured output
- proof-oriented regression coverage centered on the reasoner test pack
- a compact evaluation set for realistic CRM-style prompts

What this means in practice:

- deterministic routing still runs first
- fallback reasoning is only used after deterministic handling cannot resolve the request safely
- execution still depends on validator-approved structure and validated context

## Key Guarantees

The current layer should be treated as reliable for these guarantees:

- raw LLM output is not executed directly
- `intent`, `action`, `object_type`, references, and field payloads are normalized in Python
- `MANAGE`, `UPDATE`, and `DELETE` still require one validated target record
- conflicting `intent` and `action` are forced into clarification
- mixed-object outputs are forced into clarification
- invalid field combinations are blocked
- low-confidence executable output is clarified
- confidence never overrides stronger safety blockers
- noisy input is handled conservatively rather than aggressively

## Intentional Limits And Conservative Behavior

The current layer is intentionally conservative in these areas:

- no hidden name-based target resolution
- no broad object-support expansion through fallback reasoning
- no execution for context-free destructive prompts
- no execution for under-specified update prompts
- no hidden object switching across ambiguous context
- no broad planner-style inference

Examples that should still remain conservative:

- `update john phone num to 01012345678`
- `delete that one`
- `remove the last opp`
- `open the lead and contact`
- `do the thing we talked about`

If a future change makes these execute more eagerly, it should be treated as high-risk unless there is explicit approval and matching proof coverage.

## Important Files

Highest-signal implementation files:

- `development/ai_agent/llm/backend/intent_reasoner.py`
- `development/ai_agent/llm/backend/conversation_context.py`
- `development/ai_agent/llm/backend/intent_preclassifier.py`
- `development/ai_agent/ui/backend/service.py`

Practical importance:

- `intent_reasoner.py` is the main fallback contract, prompt, normalization, and validation surface
- `conversation_context.py` defines the compact validated context model that makes contextual resolution possible
- `intent_preclassifier.py` protects the deterministic fast path
- `service.py` is still the runtime handoff point for fallback reasoning and remains the main merge-risk file

## Important Tests

Highest-signal test entry point:

- `development/test/unit/ai_agent/backend/test_intent_reasoner.py`

That test pack is the main proof layer for:

- prompt guidance expectations
- safe executable fallback shapes
- clarification-priority behavior
- contract safety failures
- confidence-policy behavior
- noisy-input conservative handling
- fallback integration guard behavior

Additional supporting tests:

- `development/test/unit/ai_agent/backend/test_preclassifier_phase177.py`
- `development/test/unit/ai_agent/backend/test_phase229_context_resolution.py`
- `development/test/unit/ai_agent/backend/test_phase230_query_context.py`
- `development/test/unit/ai_agent/backend/test_phase226_deterministic_crud.py`

## Important Docs

Highest-signal docs for future work:

- `development/docs/llm_reasoning.md`
- `development/docs/llm_reasoning_eval.md`
- `development/docs/testing.md`
- `development/docs/codex-working-rules.md`

Practical roles:

- `llm_reasoning.md` describes the current contract and limits
- `llm_reasoning_eval.md` gives realistic evaluation cases for future quality checks
- `testing.md` defines the mandatory proof expectations for behavior changes
- `codex-working-rules.md` keeps scope, backup, and reporting discipline in place

## Merge-Risk Notes

Main merge-risk area:

- `development/ai_agent/ui/backend/service.py`

Why it matters:

- it still owns the live fallback handoff
- parallel work in `ui` can easily conflict there
- reasoning-layer changes should avoid pushing new logic into that file unless truly necessary

Low-risk future changes usually stay inside:

- `intent_reasoner.py`
- `test_intent_reasoner.py`
- narrow docs like `llm_reasoning.md` or `llm_reasoning_eval.md`

Higher-risk future changes include:

- touching `service.py`
- broadening object support
- adding new target-resolution behavior
- making destructive/update flows more eager
- changing deterministic routing order

## Practical Next Steps

Best narrow follow-up areas from the current state:

1. Tighten evaluation-driven handling for a few remaining awkward query-style noisy prompts without making them executable by default.
2. Improve clarification specificity for weak contextual phrases only where the validator can already see the likely missing object or target type.
3. Expand proof coverage around prompt-guided raw-output shapes that are close to the current safe contract but still awkward.
4. Keep the evaluation set and the main reasoner regression pack aligned whenever fallback behavior changes.
5. Avoid touching `service.py` unless a reasoning change truly cannot affect runtime behavior without it.

## Safe Vs Risky Change Types

Usually safe:

- improving normalization for already-supported object or field aliases
- improving clarification text without relaxing execution rules
- adding proof-oriented tests for known safe/conservative cases
- refining prompt guidance so it better matches existing validator rules

Usually risky:

- adding name-based target resolution
- turning ambiguous updates or deletes into executable actions
- broadening object support through fallback reasoning
- changing context resolution beyond the current validated model
- moving fallback behavior across layers without strong reason and tests
