from pathlib import Path


BULK_ACTION_JS_PATH = "development/web/frontend/static/js/bulk_action.js"


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_bulk_action_js_keeps_checkbox_selection_and_button_state_contract():
    source = _read(BULK_ACTION_JS_PATH)

    assert "function toggleAllCheckboxes(source)" in source
    assert "document.querySelectorAll('.row-checkbox')" in source
    assert "cb.checked = source.checked;" in source
    assert "function updateDeleteButtonState()" in source
    assert "deleteBtn.style.display = 'inline-block';" in source
    assert "deleteBtn.innerText = `Delete (${checkboxes.length})`;" in source
    assert "deleteBtn.style.display = 'none';" in source


def test_bulk_action_js_keeps_confirmation_and_shared_bulk_delete_endpoint():
    source = _read(BULK_ACTION_JS_PATH)

    assert "function confirmBulkDelete(objectType)" in source
    assert "const title = `Delete ${objectType}s`;" in source
    assert "showConfirmModal(title, message, () => {" in source
    assert "executeBulkDelete(ids, objectType);" in source
    assert "fetch('/bulk/delete', {" in source


def test_bulk_action_js_keeps_success_and_error_feedback_paths():
    source = _read(BULK_ACTION_JS_PATH)

    assert "showToast(data.message || `Deleted ${ids.length} items.`, false);" in source
    assert "setTimeout(() => window.location.reload(), 1500);" in source
    assert 'showToast(data.message || "Bulk delete failed.", true);' in source
    assert 'showToast("An error occurred during bulk delete.", true);' in source
