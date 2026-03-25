# Implementation Plan - Phase 158: Recycle Bin System and Data Isolation

## Goal
Implement a centralized Recycle Bin system to manage soft-deleted records and ensure that deleted data is completely isolated from Global Search and Lookup fields.

## Key Components

### 1. Data Isolation (Mandatory)
- **Global Search**: Update `SearchService` to filter out any records where `deleted_at` is not NULL.
- **Lookup Fields**: Ensure all object services (`Lead`, `Contact`, `Opportunity`, etc.) use `deleted_at == None` in their retrieval logic for lookups and list views.

### 2. Recycle Bin Backend
- **TrashService**: A new service to query all soft-deleted records across multiple models (Lead, Contact, Opportunity, Asset, Product, VehicleSpecification).
- **TrashRouter**: Endpoints for:
    - `GET /trash`: Render the Recycle Bin list view.
    - `POST /trash/{object_type}/{id}/restore`: Restore a record (set `deleted_at = NULL`).
    - `POST /trash/{object_type}/{id}/hard-delete`: Permanently delete a record from the DB.

### 3. Frontend Implementation
- **Header Update**: Add a Recycle Bin icon (Trash icon) at the far right of the top navigation bar.
- **Trash List View**: A dedicated page displaying deleted records with their object type, name, and deletion date.
- **Actions**: Provide "Restore" and "Delete Permanently" buttons for each record.

## Verification
- **Isolation Test**: Delete a record and verify it disappears from global search and all lookup dropdowns.
- **Lifecycle Test**: Delete -> View in Trash -> Restore -> Verify active status.
- **Hard Delete Test**: Delete permanently from Trash and verify DB record is gone.

## Documentation & Backups
- Maintain phase traceability in `Implementation/`, `task/`, and `Walkthrough/`.
- Backup all modified files to `.gemini/development/backups/101_199/phase158/`.
