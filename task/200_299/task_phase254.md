## Phase 254 Task

### Title
Opportunity-only chat-card Send Message parity

### Approved Scope
- Object-specific only
- Narrow scope only
- Add `Send Message` to opportunity chat-card actions
- Update opportunity card hint copy only as needed to match the new action
- Reuse the existing frontend `send_message` card-action handling and existing chat-native messaging path where possible

### Must Preserve
- Lead card actions unchanged
- Contact card actions unchanged from Phase 253
- Submit continuity unchanged
- Non-submit `OPEN_RECORD` continuity unchanged
- Selection-open continuity unchanged

### Required Tests
- Focused unit coverage for opportunity card actions and unchanged neighboring objects
- Narrow DOM-level UI coverage for opportunity card `Send Message`
- No browser automation
- No manual testing

### Documentation
- Update `development/docs/ai-agent-crud-contract.md` only as needed to reflect the new opportunity card-action expectation
