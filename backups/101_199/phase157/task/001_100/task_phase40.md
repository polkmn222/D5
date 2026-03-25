# Task: Phase 40 - Messaging, Tasks & Attachments AI Integration

## Objective
Enable the AI Agent to perform comprehensive CRUD (Create, Read, Update, Delete) operations for Messaging (MessageSend, MessageTemplate) and Tasks. Ensure robust conversational flows for these objects and integrate necessary service calls. Attachments will remain system-internal and not exposed for direct AI management.

## Sub-tasks
1. **Source Backup**: Create a full backup of AI Agent, messaging, and task services in `.gemini/development/backups/phase40/`.
2. **Models & Services Audit**:
   - Add missing `Task` model to `db/models.py`.
   - Create `task_service.py` with full CRUD methods.
   - Verify `MessageService`, `MessageTemplateService`, `AttachmentService` are present and functional.
   - Correct `TaskService.create_task` to avoid `id` conflict with `BaseService`.
3. **AI Agent Logic Extension**:
   - Update `ai_agent/backend/service.py`:
     - Extend `CONVERSATIONAL CREATE FLOW` prompt to include `Task` (needs `subject`) and `Template` (needs `name`, `content`).
     - Extend `QUERY FLOW` prompt for `Task`, `MessageTemplate`, and `MessageSend`, mapping `messages` queries to `message_sends`.
     - Extend `MANAGE` intent's `fields_list` for `Task` and `MessageTemplate`.
     - Add `CREATE`, `UPDATE`, `DELETE` logic for `Task` and `MessageTemplate`.
     - Add `QUERY` logic for `MessageSend`.
4. **Unit Testing**:
   - Create `test_ai_messaging_task_crud.py` to verify full CRUD lifecycles for Tasks and MessageTemplates, and query for MessageSends.
   - Ensure all AI Agent related unit tests pass after changes.
5. **Validation**: Confirm conversational flows and CRUD operations work correctly via AI Agent.

## Completion Criteria
- Comprehensive backup for Phase 40 is created.
- AI Agent supports full CRUD for Tasks and MessageTemplates.
- AI Agent can query MessageSends.
- All AI Agent unit tests (including new ones) pass 100%.
- Phase 40 documentation is generated.