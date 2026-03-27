## Phase 253 Task

### Title
Contact-only chat-card Send Message parity

### Approved Scope
- Object-specific only
- Narrow scope only
- Add `Send Message` to contact chat-card actions
- Update contact card hint copy only as needed to match the new action
- Reuse the existing frontend `send_message` card-action handling and existing chat-native messaging path where possible

### Must Preserve
- Lead card actions unchanged
- Opportunity card actions unchanged
- Submit continuity unchanged
- Non-submit `OPEN_RECORD` continuity unchanged
- Selection-open continuity unchanged

### Required Tests
- Focused unit coverage for contact card actions and unchanged neighboring objects
- Narrow DOM-level UI coverage for contact card `Send Message`
- No browser automation
- No manual testing

### Documentation
- Update `development/docs/ai-agent-crud-contract.md` only as needed to reflect the new contact card-action expectation
