# LLM Reasoning Layer

## Purpose

This document describes the current fallback LLM reasoning layer used by `development/ai_agent`.

Its purpose is narrow:

- preserve deterministic routing as the first path
- use LLM reasoning only after deterministic handling cannot resolve the request safely
- convert ambiguous, contextual, or noisy requests into validated structured output
- prefer clarification over risky execution

This layer is accuracy-first and conservative. It is not a general planner and it does not replace deterministic CRUD/query routing.

## Scope And Runtime Position

The runtime still prefers deterministic handling first.

Current order in practice:

1. explicit contextual helpers already owned by the runtime
2. deterministic CRUD/query routing
3. simple clarification from `IntentReasoner.clarify_if_needed()`
4. lightweight rule-based preclassification from `IntentPreClassifier.detect()`
5. structured LLM fallback reasoning
6. Python-side normalization and validation
7. `_execute_intent()` with validated payload only

The fallback reasoner is used only after deterministic handling has failed to produce a safe result.

## Why The Narrow `service.py` Hook Exists

The structured reasoner lives under `development/ai_agent/llm/backend/`, but the live fallback caller still sits in:

- `development/ai_agent/ui/backend/service.py`

That narrow hook is still required because `process_query()` owns:

- the fallback LLM call
- the handoff into `IntentReasoner`
- the final validated payload passed to `_execute_intent()`

The hook is intentionally narrow:

- deterministic routing remains unchanged
- no frontend behavior is owned here
- no routing expansion is introduced
- the validator remains the authoritative safety layer

## File Responsibilities

### `development/ai_agent/llm/backend/intent_reasoner.py`

`intent_reasoner.py` owns the fallback reasoning contract and the fallback validation rules.

Current responsibilities:

- build the fallback structured-reasoning prompt
- explain the expected JSON shape to the model
- normalize `intent`, `action`, `object_type`, field names, and context-reference hints
- apply conservative alias handling for noisy English phrasing inside the current safe scope
- resolve allowed context references from Python-owned conversation state
- validate raw LLM output before execution
- enforce executable vs non-executable rules
- enforce clarification-priority rules
- downgrade unsafe or under-specified output into safe `CHAT` clarification

It does not perform CRUD execution directly.

### `development/ai_agent/llm/backend/conversation_context.py`

`conversation_context.py` owns the compact conversation state used by fallback reasoning.

Current responsibilities:

- remember the last created record
- remember the last active record
- remember recent query results
- remember current selection state
- build a compact reasoning-context payload for the fallback reasoner
- expose limited safety hints such as multi-selection state

The context model is intentionally compact. Fallback reasoning is only considered safe within this validated context model.

### `development/ai_agent/llm/backend/intent_preclassifier.py`

`intent_preclassifier.py` remains part of the deterministic fast path.

Current responsibilities:

- normalize obvious action and object aliases
- detect simple `QUERY`, `OPEN_FORM`, or safe `CHAT` cases
- keep obvious requests out of the fallback LLM path
- let ambiguous or context-heavy requests continue to fallback reasoning

It is not the structured reasoner and it does not replace the validator.

## Structured Reasoning Contract

The fallback prompt asks the model for a structured JSON object. The validator currently recognizes these fields:

- `intent`
- `action`
- `object_type`
- `filters`
- `fields_to_update`
- `context_reference`
- `resolved_reference`
- `requires_clarification`
- `clarification_question`
- `confidence`
- `text`
- `sql`

These fields are not all required for every result. The contract is practical rather than fully declarative: the validator defines which combinations are acceptable.

### Practical Field Expectations

Common expectations enforced by validation:

- `intent` is required for meaningful fallback output.
- `action` is optional, but if present it must agree with `intent`.
- `object_type` is required for executable non-chat outcomes.
- `filters` are allowed for `QUERY`.
- `fields_to_update` are required for `CREATE` and `UPDATE`.
- `context_reference` is allowed when the model is pointing to existing validated conversation context.
- `resolved_reference` is allowed when the output identifies one specific record.
- `requires_clarification` and `clarification_question` take priority over executable shape.
- `confidence` is always normalized and used for conservative execution gating.
- `text` is used for safe `CHAT` output.
- `sql` is not accepted for create/update flows.

## Executable Vs Non-Executable Outcomes

The validator treats fallback outputs in two broad categories.

### Executable Outcomes

Executable outcomes are allowed only when the output is otherwise safe and sufficiently complete.

Current executable intents:

- `QUERY`
- `CREATE`
- `UPDATE`
- `DELETE`
- `MANAGE`

Current executable requirements include:

- valid normalized `intent`
- no conflicting `action`
- one clear `object_type` for the action
- no invalid field combinations
- a validated target record for `MANAGE`, `UPDATE`, and `DELETE`
- required fields for `CREATE` and `UPDATE`
- sufficient confidence for execution

### Non-Executable Outcomes

Fallback output is forced into non-executable clarification when:

- the output is malformed
- intent is invalid or missing
- `intent` and `action` conflict
- the object is mixed or unclear
- the target record is unresolved
- required fields are missing
- field combinations are invalid
- `requires_clarification` is set
- confidence is too low for safe execution

In these cases the validator returns a safe `CHAT` response instead of passing through risky structure.

## Python-Side Normalization And Validation

Raw LLM output is never executed directly.

Before `_execute_intent()` runs, the validator currently:

- normalizes `intent`
- reconciles `action` against `intent`
- normalizes `object_type`
- normalizes field keys such as common update-field aliases
- normalizes context-reference hints into the supported reference model
- clamps confidence into the `0.0` to `1.0` range
- assigns an explicit confidence band: `low`, `medium`, or `high`
- resolves supported references from trusted conversation context
- blocks invalid executable combinations
- converts unsafe output into clarification-oriented `CHAT`

The validator is authoritative. Prompt guidance reinforces these rules but does not replace them.

## Clarification And Refusal Behavior

Clarification is not an error path. It is the normal safe outcome when fallback reasoning cannot justify execution.

The current validator prefers clarification when it sees:

- conflicting `intent` and `action`
- mixed-object outputs
- unresolved or mismatched record targets
- multiple possible selected records
- invalid field combinations
- missing required fields for `CREATE` or `UPDATE`
- low-confidence executable outputs
- medium-confidence outputs that remain ambiguous
- explicit `requires_clarification`

Clarification text is intentionally specific and conservative. It should ask for:

- one object
- one record
- a name, ID, or single clear selection
- restatement of the action when confidence is too low

The reasoner should not imply hidden record selection or unsupported lookup behavior.

## Contextual Reference Handling

Context references are resolved only from Python-owned conversation context, not from free-form model guesses.

Supported reference categories inside the current safe model:

- `last_created`
- `last_record`
- `selection`
- `query_result`

Practical examples:

- `the one I just created`
  - resolves through `last_created`
- `that one`
  - may resolve through `last_record` only when safe context exists
- `the last one`
  - may resolve through `last_record` or `query_result` only when safe context exists
- recent ranked list references
  - may resolve through `query_result`

Current limits:

- no hidden object switching
- no free-form name resolution beyond validated context
- no execution when context points to multiple possible records
- no execution when the resolved object conflicts with the requested object

## Noisy-Input Robustness

The fallback validator now supports limited noisy English normalization inside the current safe scope.

This includes conservative handling for:

- casual phrasing
- shorthand such as `opp`
- incomplete grammar
- mild typos and informal wording
- indirect references such as `i just added` or `from before`
- field aliases such as `phone num`

Important limit:

- noisy-input support is normalization-only within the current validated context model

It does not introduce:

- broader object support
- hidden target inference
- name-based lookup beyond validated context
- eager execution of under-specified prompts

If noisy input still lacks a clear object, target, or safe structure, the result must stay in clarification.

## Confidence Policy

Confidence handling is explicit and conservative.

The validator currently uses:

- `low` confidence
- `medium` confidence
- `high` confidence
- one execution threshold for executable outcomes

Current policy:

- `CHAT` remains permissive even at low confidence
- executable intents must meet the execution threshold
- low-confidence executable output is clarified
- medium-confidence output that remains ambiguous is clarified
- high-confidence executable output is still blocked if any stronger safety rule fails

Confidence never overrides stronger safety blockers such as:

- unresolved target record
- mixed-object output
- conflicting `intent` and `action`
- invalid field combinations

## Prompt Guidance

The fallback prompt is intentionally narrow and implementation-facing.

It now explicitly guides the model on:

- the distinction between `intent` and `action`
- choosing one `object_type` for executable output
- preferring clarification when the target is unclear
- preferring clarification when confidence is insufficient
- handling noisy English phrasing conservatively

The prompt includes only a very small number of aligned examples. Their role is to stabilize structured output, not to create a large example library.

Current prompt design principles:

- validator rules remain authoritative
- prompt guidance should reduce confusion, not add new behavior
- examples must stay inside the existing safe scope
- ambiguous or unsafe requests should be guided toward clarification

## Proof-Oriented Regression Strategy

The main proof-oriented regression pack for this layer is:

- `development/test/unit/ai_agent/backend/test_intent_reasoner.py`

That file is organized to lock down the current guarantees around:

- prompt guidance expectations
- safe executable outcomes
- target safety and clarification priority
- contract safety failures
- confidence-policy behavior
- noisy English input handling
- prompt-guided shape stability
- fallback integration guard behavior

The test philosophy is deliberate:

- tests should prove strengthened behavior, not only different behavior
- tests should show both safe supported outcomes and conservative refusal behavior
- tests should include clean commands, mildly noisy English input, and ambiguous real-user phrasing
- coverage preservation is treated as more important than cosmetic cleanup

## Exact Implementation And Test Files

Current implementation files directly involved in this reasoning path:

- `development/ai_agent/llm/backend/intent_reasoner.py`
- `development/ai_agent/llm/backend/conversation_context.py`
- `development/ai_agent/llm/backend/intent_preclassifier.py`
- `development/ai_agent/ui/backend/service.py`

Current related tests:

- `development/test/unit/ai_agent/backend/test_intent_reasoner.py`
- `development/test/unit/ai_agent/backend/test_preclassifier_phase177.py`
- `development/test/unit/ai_agent/backend/test_phase229_context_resolution.py`
- `development/test/unit/ai_agent/backend/test_phase230_query_context.py`
- `development/test/unit/ai_agent/backend/test_phase226_deterministic_crud.py`

## Known Limits And Out-Of-Scope Behavior

The following remain intentional limits of the current design:

- deterministic routing remains the first path
- the reasoning layer is not a broad platform planner
- context resolution is only safe within the current compact validated context model
- noisy-input support is conservative and normalization-only
- object support is not broadened here
- fallback reasoning does not replace deterministic CRUD parsing
- prompt guidance does not override validator rules
- manual testing is out of scope

## Merge-Risk Note

`development/ai_agent/ui/backend/service.py` remains the highest merge-risk file related to this reasoning path because it owns the runtime fallback handoff.

Future edits should keep that file narrowly scoped unless broader approval is explicitly given.
