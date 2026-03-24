# System Blueprint

## Technical Stack
- **Framework**: FastAPI (Python 3.12+)
- **ORM**: SQLAlchemy 2.0+ (Declarative Mapping)
- **Database**: SQLite (Local file-based)
- **Frontend**: Jinja2 Templates + Vanilla CSS (Salesforce Lightning Design System inspiration)
- **AI Integration**: Groq/Cerebras (Llama 3 / 70B models)
- **Testing**: Pytest

## Architecture Overview
The system follows a modular Service-Oriented Architecture (SOA):
1. **Models (`models.py`)**: Defines Salesforce-aligned objects with 18-digit IDs and auto-timestamps.
2. **Services (`app/services/`)**: Contains atomic business logic (Lead conversion, data seeder, etc.).
3. **API Routes (`app/api/web_router.py`)**: Handles HTTP requests and template rendering.
4. **Utilities (`app/utils/`)**: Reusable logic like Salesforce ID generation (`sf_id.py`).

## UI Architecture (Detail Views)
- **Tabbed Interface**: Every detail page must implement a Salesforce-style tabbed UI.
- **Mandatory Tabs**: `Details` (Field-level data) and `Related` (Child record lists) are mandatory for all objects.
- **Path Component**: Leads and Opportunities must display a visual progress path (Status bar).
- **Two-Column Layout**: Detail fields should be presented in a responsive two-column grid.

## Data Flow
1. **Request Intake**: FastAPI router receives user interaction (e.g., Lead Conversion).
2. **Logic Execution**: Router delegates to the appropriate Service (e.g., `LeadService.convert_lead`).
3. **Database Mutation**: SQLAlchemy ORM commits changes to `crm.db`.
4. **UI Update**: Router returns a `RedirectResponse` or `TemplateResponse` to refresh the modal or list view.

# END FILE
