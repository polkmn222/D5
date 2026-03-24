# UI Standards

## Object Detail Views
To ensure unity across all objects in the CRM, the following standards must be followed for Detail views:

### 1. Tabs and Page Framing

- Detail pages should preserve the established `Details`, `Related`, and `Activity` tab structure used by the shared detail templates.
- Shared behaviors defined in `frontend/templates/base.html` remain the default source for inline editing, footer actions, and shared scripts.

### 2. Pencil Buttons and Inline Editing

- Use the pencil emoji (`✏️`) inside a `span.sf-pencil-icon` for inline-edit affordances.
- Keep the icon inside the `sf-editable-field` container so field-level interaction stays consistent.
- Standard fields should trigger `toggleInlineEdit(...)` from the editable container.
- Lookup fields should trigger `toggleLookupEdit(...)` from the pencil icon and call `event.stopPropagation()`.
- Pencil icons should hide while the page is in edit mode through the shared `.sf-editing` body state.

### 3. Multi-Field Editing

- Users should be able to open multiple field editors before saving.
- The shared `#sf-edit-footer` action area is the standard save and cancel surface for pending inline edits.

### 4. Bulk Actions

- Bulk deletion should use checkbox-driven selection within a modal or list-oriented bulk action surface.
- The delete CTA should appear only when one or more records are selected.
- Bulk actions should continue to use the shared `bulk_action.js` helper and the `/bulk/delete` endpoint.
- Utility lists and messaging-related lists should follow the same selection and confirmation pattern as core CRM objects.

### 5. Layout and Empty-State Rendering

- Use the standard responsive two-column field grid for detail sections.
- Place labels above values or inline within the established detail card layout.
- Render null or missing values as blank output through the shared formatting pattern rather than exposing `None`, `N/A`, or broken placeholders.

### 6. Responsive Consistency

- Desktop and mobile layouts should preserve tab usability, field readability, and action discoverability.
- New object pages should reuse shared detail patterns before introducing object-specific deviations.
