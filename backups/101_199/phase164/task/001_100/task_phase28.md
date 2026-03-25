# Task: Phase 28 - Routing Fixes & Network Accessibility

## Objective
Address the `ERR_CONNECTION_REFUSED` error and fix incorrect routing that resulted in 404 errors for certain endpoints. Ensure the server is accessible through the gateway by binding to `0.0.0.0` and standardize path prefixes across all routers.

## Sub-tasks
1. Update `run_crm.sh` to bind Uvicorn to `0.0.0.0` for external accessibility.
2. Remove redundant path prefixes (e.g., `/leads`, `/products`, `/assets`) from individual router files to avoid double-prefixing (e.g., `/leads/leads`).
3. Standardize route decorators in `lead_router.py`, `product_router.py`, `asset_router.py`, `contact_router.py`, `opportunity_router.py`, and `message_template_router.py`.
4. Adjust `api_router.py` to handle `vehicle_spec_router` without a prefix, as it manages multiple top-level categories (Brands and Models).
5. Verify connectivity and correct routing for key endpoints (`/`, `/leads/`, `/vehicle_specifications`).

## Completion Criteria
- Root `run_crm.sh` starts the server on `0.0.0.0:8000`.
- All major functional endpoints return HTTP 200 OK.
- No "refused to connect" errors are encountered when accessing the specified host/port.
- Phase 28 documentation is generated.