# Task: Phase 35 - Contact CRUD & Batch Integration

## Objective
Verify and standardize the CRUD (Create, Read, Update, Delete) functionality for the Contact object. Ensure that advanced features like inline editing (batch-save) are implemented and functional across both Contacts and Leads for UI consistency.

## Sub-tasks
1. **Audit Contact Logic**: Review `ContactService` and `contact_router.py` to ensure alignment with standard patterns.
2. **Implement Batch Save**:
   - Add `/{contact_id}/batch-save` endpoint to `contact_router.py`.
   - Add `/{lead_id}/batch-save` endpoint to `lead_router.py`.
   - Add `/{opp_id}/batch-save` endpoint to `opportunity_router.py`.
3. **Standardize Update Routes**: Unify update routes to support the default `/{id}` path (POST) for broader compatibility with standard templates.
4. **Verification via Testing**:
   - Run `pytest test/unit/test_contacts.py` to confirm basic CRUD operations.
   - Perform manual verification of the "Edit" pencil icon and the global "Save" footer functionality in Detail views.
5. **Ensemble AI Check**: Confirm the AI Agent can effectively query and manage contacts.

## Completion Criteria
- Contact CRUD tests pass 100%.
- Batch save (JSON update) endpoints are present and functional for Contacts, Leads, and Opportunities.
- Detail views allow inline editing via pencil icons with a functional global Save footer.
- Phase 35 documentation is generated.