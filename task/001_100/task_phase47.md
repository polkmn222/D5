# Task Phase 47: CRUD Reliability & Data Integrity Fix

## Task List
- [x] Identify root cause of CRUD "not normal" behavior (None-overwrite bug).
- [x] Fix `BaseService.update` in `backend/app/services/base_service.py` to only update non-None values.
- [ ] Create `tests/unit/test_api_crud_postgres.py` with `TestClient` for comprehensive API verification.
- [ ] Run the test suite against a test database (`TEST_MODE=1`).
- [ ] Verify that Lead creation, update, and conversion work as expected.
- [ ] Verify that Contact creation and update work as expected.
- [ ] Verify that Opportunity, Asset, and Product CRUD work as expected.
- [ ] Verify that Brand and Model CRUD work as expected.
- [ ] Audit all object routers to ensure field names match between Jinja2 templates and POST parameters.
- [ ] Finalize documentation of the fix.
