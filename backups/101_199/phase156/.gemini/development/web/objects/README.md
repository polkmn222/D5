# Web Objects Guide

## Scope
- This folder contains self-contained modules for each CRM object (Lead, Contact, Opportunity, etc.).
- Each object "owns" its own backend logic, routing, and templates to minimize cross-module dependencies.

## Standard Object Structure
Each object folder (e.g., `lead/`) must follow this pattern:
- `backend/service.py`: Class-based business logic using `@staticmethod` and explicit error handling.
- `backend/router.py`: Class-based FastAPI router managing the object's endpoints.
- `frontend/templates/`: Jinja2 templates specific to the object.
- `frontend/static/js/`: (Optional) JavaScript specific to the object.

## Mandatory Rules
1. **Atomics First**: Every object module must be as independent as possible.
2. **Class-Based Services**: All service functions must be defined as static methods within a class.
3. **Error Resilience**: Every backend function MUST be wrapped in a `try-except` block.
4. **Naming Lookups**: Lookup fields should be named clearly (e.g., "Account") and must NOT contain "ID" or "id" in the label.
5. **No Nulls**: Display missing values as a blank space in the UI.

## Integration
- Modular routers must be registered in `web/core/backend/api/api_router.py`.
- Object templates are automatically discovered by the core template engine.
