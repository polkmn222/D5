# CRM Technical Skills

## 1. Database Mastery (SQLite + SQLAlchemy)

* **Atomic Operations**: Implementing isolated CRUD functions to prevent side effects.
* **Advanced Mapping**: Handling complex relationship mapping for Accounts, Contacts, Assets, and Products.
* **Migration Safety**: Ensuring schema integrity during AI-driven data seeding.

## 2. Salesforce-Style UI/UX Engineering

* **Component Architecture**: Building "Lightning-like" responsive interfaces using Vanilla CSS and Jinja2.
* **Asset Organization**:
* Folderizing HTML templates by object (e.g., `templates/account/`).
* Managing object-specific JavaScript logic in dedicated modules.



## 3. High-Granularity Backend Development

* **Router Specialization**: Mapping exactly one class to one `@router` for extreme isolation.
* **Service Logic**: Implementing business logic within `@staticmethod` class structures in the `service/` layer.
* **Stability-First Coding**: Preventing regression by separating features into as many Python files as logically possible.

## 4. AI Orchestration & Data Seeding

* **Model Integration**: Utilizing Groq/Cerebras (Llama 3) for real-time CRM intelligence.
* **Automated Summarization**: Generating rapid lead/opportunity assessments and sentiment analysis.
* **Theme-based Seeding**: Synthesizing realistic, industry-specific JSON data for SQLite ingestion.

## 5. Messaging & Integration (SureM)

* **SMS Infrastructure**: Handling SureM API requests with asynchronous status tracking.
* **Validation**: Enforcing provider-specific formatting and robust error handling for external APIs.

## 6. Execution Workflow (The Antigravity Process)

### Phase 1: Planning

* Update `task.md` and obtain approval for `implementation_plan.md`.

### Phase 2: Atomic Execution

* **Step-by-Step Construction**: Models → Services (Class/Static) → Routes (Class/Router) → UI (Object-specific folders).
* **Mandatory Safety**: Wrap every function in `try-except` and connect to browser-based alert systems.

### Phase 3: Verification

* Execute Pytest-driven unit tests for all core services.
* Verify Salesforce aesthetic alignment and UI responsiveness.

### Phase 4: Completion & Archiving

* Generate a comprehensive walkthrough of the phase.
* Execute the global backup policy (Phase-specific folders in `backups/`).
