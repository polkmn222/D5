# Verification Spec

## Definition of Success
A feature is considered "Done" only when:
1. All core functionality requirements are met.
2. UI matches Salesforce design aesthetics (Modals, spacing, colors).
3. **Tabs**: Every record detail page must have visible and functional `Details` and `Related` tabs.
4. Unit tests pass (No regressions).
5. Phase backup is successfully executed.

## Test Checklist
- [ ] **ID Integrity**: Every new record must have a valid 18-character Salesforce-style ID.
- [ ] **Timestamp Auditing**: `CreatedDate` and `LastModifiedDate` must be automatically populated and non-editable via UI.
- [ ] **Validation**: Required fields must trigger a red banner/border error instead of a server crash.
- [ ] **Lead Lifecycle**: Converting a Lead must create an Account, Contact, and Opportunity with inherited Brand/Model interests.
- [ ] **Import Logic**: CSV files must be processed without duplicate IDs or blank essential fields.

## Edge Cases to Verify
- Null lookup values (e.g., Lead without a Campaign).
- Duplicate VINs in Assets (Must trigger a clean error).
- Partial CSV imports (Transaction atomicity).

# END FILE
