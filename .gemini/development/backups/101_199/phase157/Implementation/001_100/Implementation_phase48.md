# Phase 48 - AI Agent Intent Robustness (Lead Variations)

## Objective
Enhance AI Agent natural language robustness so that variations such as:

- "리드 만들고 싶어"
- "리드를 만들어줘"
- "create lead"
- "I want to create laed" (typo)
- "show all lead"
- "all lead"

are consistently interpreted with correct structured JSON intent.

Target: Improve CREATE and QUERY intent reliability for Lead object.

---

## Architecture Strategy

### 1. Pre-Intent Normalization Layer
Before LLM ensemble call:
- Lowercase normalization
- Basic typo correction (lead, laed → lead)
- Synonym mapping ("만들", "create", "add" → CREATE)
- Query keywords ("show", "all", "list", "전체" → QUERY)

This reduces LLM ambiguity and improves score consistency.

---

### 2. Intent Hint Injection in System Prompt
System prompt updated with explicit examples:

Examples:
- "create lead" → CREATE + object_type=lead
- "show all lead" → QUERY + object_type=lead
- "리드 전체 보여줘" → QUERY + object_type=lead

---

### 3. Ensemble Scoring Reinforcement
When multiple models respond:
- If object_type=lead and intent in {CREATE, QUERY}
- Boost score by +0.05

Ensures consistent selection of structured response.

---

### 4. MCP Tool Integration (sequential-thinking)
Use sequential-thinking to:
- Step 1: Detect action verb
- Step 2: Detect object keyword
- Step 3: Resolve ambiguity
- Step 4: Construct structured JSON

This is used internally before returning final JSON.

---

## Expected Behavior

Input: "I want to create laed"
Output:
{
  "intent": "CREATE",
  "object_type": "lead",
  "text": "Sure. Please provide last name and status.",
  "score": 0.92
}

Input: "all lead"
Output:
{
  "intent": "QUERY",
  "object_type": "lead",
  "sql": "SELECT ... FROM leads WHERE deleted_at IS NULL ...",
  "score": 0.90
}
