# UI Standards

## Object Detail Views
To ensure unity across all objects in the CRM, the following standards must be followed for Detail views:

### 1. Pencil Buttons (Inline Editing)
- **Appearance**: Use the pencil emoji (✏️) wrapped in a `span` with class `sf-pencil-icon`.
- **Structure**: The pencil icon must be nested inside the `sf-editable-field` container.
- **Interaction**:
    - For standard fields, the `sf-editable-field` div should have `onclick="toggleInlineEdit(...)"`.
    - For lookup fields, the pencil icon should have `onclick="toggleLookupEdit(...)"` and `event.stopPropagation()`.
- **Unity**: All objects (Leads, Contacts, Opportunities, etc.) MUST use the exact same implementation pattern for pencil buttons.
- **Visibility**: Pencil icons must be hidden when any field is being edited (when `body` has `.sf-editing` class). This is enforced via `interactions.css`.

### 2. Multi-Field Editing
- Users must be able to click multiple pencil buttons to edit multiple fields simultaneously.
- The global `sf-edit-footer` (Save/Cancel) will handle batch updates for all modified fields.

### 3. Bulk Deletion
- Bulk deletion UI should always use a modal containing a list of records with checkboxes.
- A "Delete (N)" button should only appear when one or more records are selected.
- All bulk delete actions must use the standard `bulk_action.js` helper and the `/bulk/delete` endpoint.
- For consistency, even utility-style lists (like Templates in the Send Message tab) must follow this pattern.

### 4. Layout
- Use the standard responsive two-column grid for fields.
- Labels should be on top, values below/inline.
- Null or missing values must be displayed as a blank space (`&nbsp;`) to maintain grid structure.
