# GEMINI.md - AI Ready CRM (D4)

## Project Overview
**AI Ready CRM** is a modern, AI-enhanced Customer Relationship Management system specifically tailored for the **automotive industry**. It is built with **FastAPI** for the backend, **SQLAlchemy** for ORM with **SQLite** as the database, and **Jinja2** templates for the web interface. The project emphasizes AI-driven insights, recommendations, and efficient messaging workflows.

### Key Technologies
- **Framework:** FastAPI (Python 3.x)
- **Database:** SQLite + SQLAlchemy
- **Template Engine:** Jinja2 + HTMX (for dynamic UI updates)
- **AI Services:** Cerebras (Primary) and Groq (Fallback) for real-time summaries and insights.
- **Styling:** CSS + Vanilla JS (Standard CRM look-and-feel).

---

## Core Architecture

### 1. Project Structure
- `app/main.py`: The entry point for the FastAPI application.
- `app/api/`: Contains route definitions organized by functional areas (Web UI, Forms, Messaging).
- `app/services/`: The business logic layer, where services handle data processing, AI interactions, and external integrations.
- `app/models.py`: Defines the SQLAlchemy models for all CRM entities.
- `app/database.py`: Handles database engine initialization and session management.
- `app/templates/`: Jinja2 templates for rendering the UI.
- `app/static/`: Static assets (CSS, JS, Images).
- `scripts/`: Python scripts for seeding data and other utility tasks.
- `tests/`: Automated tests for the application logic.

### 2. Domain Models
- **Standard CRM:** Account, Contact, Lead, Opportunity, Campaign, Product, Task.
- **Automotive-Specific:** Vehicle Specification (Brand, Model), Asset (VIN-based tracking).
- **Messaging:** Message Template, Message (SMS, LMS, MMS).
- **BaseModel:** All models inherit from a `BaseModel` providing `created_at`, `updated_at`, and `deleted_at` (Soft Delete support).

### 3. AI Capabilities
- **Summarization:** One-line summaries for contacts/leads using Cerebras/Groq.
- **Insights:** Opportunity analytics and recommendations for deals.
- **Messaging:** AI-assisted message template creation and selection.

---

## Building and Running

### Prerequisites
- Python 3.8+
- `.env` file with `CELEBRACE_API_KEY` and/or `GROQ_API_KEY`.

### Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Direct run
uvicorn app.main:app --reload

# Using the launcher script (Salesforce Benchmark Mode)
./run_crm.sh
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_contacts.py
```

### Seeding Data
The application includes several scripts for generating test data:
- `scripts/seed_phase22.py`: Generates master data.
- `recreate_templates.py`: Initializes message templates.

---

## Development Conventions

### 1. Database & Migrations
- The application uses `Base.metadata.create_all(bind=engine)` on startup to initialize tables. 
- For schema changes, existing tables might need to be dropped or migrated manually (check `tmp/migrate_db.py` for examples).

### 2. Soft Deletion
- All primary entities support soft deletion via the `deleted_at` field. 
- Always filter queries with `.filter(Model.deleted_at == None)` unless explicitly retrieving deleted records.

### 3. API & Routing
- `web_router.py` handles the main UI views.
- `form_router.py` handles object creation and update forms.
- `messaging_router.py` manages the messaging interface and template logic.

### 4. UI Patterns
- **List Views:** Standardized `list_view.html` for all objects.
- **Detail Views:** Standardized `detail_view.html` with support for "Path" (progress bars) and related lists.
- **Modals:** Object creation and editing are typically handled via modals (`object_form.html`).

---

## TODO / Known Gaps
- Implement a robust migration tool (e.g., Alembic).
- Expand test coverage for AI and messaging services.
- Refine the restore logic in several services where it remains simple or incomplete.


# Automotive CRM Agent Definition

## Identity

* **Name**: Antigravity Automotive CRM Specialist
* **Mission**: Build a premium, Salesforce-aligned Automotive CRM (AutoCRM) focusing on Account, Contact, Asset, and Product mapping for the vehicle industry.
* **Tone**: Professional, proactive, and meticulous regarding code quality and architectural integrity.

## Mandatory Rules (USER MANDATE)

* **Granular Architecture & Stability**:
* **Python Modularization**: Decompose Python code into as many files/modules as possible to ensure that deployment of one feature does not break existing functionality.


* **Frontend Organization**:
* **HTML Templates**: Templates must be folderized by object (e.g., `templates/account/`, `templates/asset/`).
* **JavaScript Management**: JS functions must be refactored and managed by object-specific modules.


* **Field & Lookup Logic**:
* **Naming**: Lookup fields MUST NOT contain "ID" or "id" (e.g., use "Account"). Clean labels only; redundant "Id" fields must be removed.
* **Navigation**: All record names in search results or "Recent Records" must be clickable lookups navigating to the record's detail page.
* **Optionality**: All fields created from this point forward are optional (non-mandatory).


* **Display & Formatting**:
* **Null Values**: All null or missing values MUST be displayed as a blank space to maintain the UI grid structure (no "None", "N/A", etc.).
* **Language**: No Korean text allowed. All UI, code comments, and documentation must be in English.


* **Error & State Management**:
* **Error Handling**: Every Python function must be wrapped in a `try-except` block. Errors must be reported to the user via browser alert/toast notifications.
* **Placeholders**: Functions "under construction" (e.g., Messaging) must trigger a "Coming Soon" alert/toast instead of an error page.



## Core Rules

1. **Atomics First**: Every module, button, and function must be designed as an atomic, independent unit.
2. **Phase & Documentation Management**:
* Increment phase numbers for every major execution.
* All core rules and skills must be consolidated into `agent.md` and `skill.md`. These files are the absolute authority.


3. **Comprehensive Backup Policy**:
* At the end of each phase, consolidate EVERY file (including `implementation_plan.md`) into the `backups/` folder.
* Follow the naming convention: `module_phaseN.py` (or relevant extension) within phase-specific subfolders.


4. **Validation & Transparency**:
* **Unit Testing**: Mandatory for all core services. Run tests before deployment and report results.
* **Confirmation**: Always request user approval with a detailed `implementation_plan.md` before executing changes.



## Technical Architecture (from Blueprint)

* **Framework**: FastAPI (Python 3.12+)
* **ORM**: SQLAlchemy 2.0+ (Declarative Mapping)
* **Database**: SQLite (Local file-based)
* **Frontend**: Jinja2 Templates + Vanilla CSS (Inspired by Salesforce Lightning Design System)
* **AI Integration**: Groq/Cerebras (Llama 3 / 70B models)

## Design Principles (from Spec)

1. **Salesforce Benchmarking**: Strictly emulate Salesforce aesthetics ("Similar but unique" feel).
2. **Standard Layouts**:
* **Navigation**: Details, Related, and Activity tabs are mandatory for every object record page.
* **Grid**: Detail fields MUST use a responsive two-column layout (Label on top, Value below/inline).


3. **Visual Progress**: Leads and Opportunities must include a visual path component (Status bar) to track progress.