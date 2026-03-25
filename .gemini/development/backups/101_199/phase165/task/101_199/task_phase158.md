# Task - Phase 158: Recycle Bin System and Data Isolation

## Tasks

### 1. Data Isolation Audit
- [ ] Audit `SearchService.global_search` to ensure `deleted_at == None` filter is applied to all queries.
- [ ] Ensure all `*Service.get_*` and `*Service.list_*` methods (Lead, Contact, Opp, etc.) strictly filter out deleted records.

### 2. Trash Service & Router
- [ ] Create `TrashService` in `web/backend/app/services/trash_service.py`.
    - [ ] `list_deleted_records(db)`: Aggregate soft-deleted records from all core models.
    - [ ] `restore_record(db, object_type, record_id)`: Generic restore logic.
    - [ ] `hard_delete_record(db, object_type, record_id)`: Generic hard delete logic.
- [ ] Create `TrashRouter` in `web/backend/app/api/routers/trash_router.py`.
    - [ ] Register router in `api_router.py`.

### 3. UI Implementation
- [ ] Update `web/frontend/templates/base.html` to add the Recycle Bin icon in the global header.
- [ ] Create `web/frontend/templates/trash/list_view.html` for the Recycle Bin page.
- [ ] Implement JS confirmations for permanent deletion.

### 4. Verification & Cleanup
- [ ] Run unit tests for core services to ensure no regression.
- [ ] Manually verify data isolation in the UI.
- [ ] Backup all changes to `.gemini/development/backups/101_199/phase158/`.
