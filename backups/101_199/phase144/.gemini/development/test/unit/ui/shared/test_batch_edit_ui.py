import re
from pathlib import Path

import pytest

APP_ROOT = next(path for path in Path(__file__).resolve().parents if path.name == "development")
TEMPLATE_DIR = APP_ROOT / "web" / "frontend" / "templates"
MESSAGE_TEMPLATE_DIR = APP_ROOT / "web" / "message" / "frontend" / "templates"

EDITABLE_DETAIL_FILES = [
    "leads/detail_view.html",
    "contacts/detail_view.html",
    "opportunities/detail_view.html",
    "brands/detail_view.html",
    "models/detail_view.html",
    "products/detail_view.html",
    "assets/detail_view.html",
    "message_templates/detail_view.html",
    "detail_view.html",
]


def resolve_template_path(file_path: str) -> Path:
    if file_path.startswith("messages/") or file_path.startswith("message_templates/"):
        return MESSAGE_TEMPLATE_DIR / file_path
    return TEMPLATE_DIR / file_path

@pytest.mark.parametrize("file_path", EDITABLE_DETAIL_FILES)
def test_batch_edit_attributes_exist(file_path):
    """Verify that lookup edit containers have the required data attributes for batch editing."""
    full_path = resolve_template_path(file_path)
    assert full_path.exists(), f"{full_path} does not exist"

    with full_path.open("r") as handle:
        content = handle.read()
        
        # Check for data-lookup-type and data-initial-id and data-initial-name
        # These are added to div id="edit-..."
        pattern = r'id="edit-[^"]+"[^>]*data-lookup-type'
        assert re.search(pattern, content) is not None, f"data-lookup-type missing in {file_path}"
        
        assert 'data-initial-id' in content, f"data-initial-id missing in {file_path}"
        assert 'data-initial-name' in content, f"data-initial-name missing in {file_path}"

@pytest.mark.parametrize("file_path", EDITABLE_DETAIL_FILES)
def test_batch_edit_triggers(file_path):
    """Verify that clicking a value or pencil icon triggers the batch edit logic."""
    full_path = resolve_template_path(file_path)
    assert full_path.exists(), f"{full_path} does not exist"

    with full_path.open("r") as handle:
        content = handle.read()
        
        # Check for toggleInlineEdit or toggleLookupEdit
        assert 'toggleInlineEdit' in content, f"toggleInlineEdit missing in {file_path}"
        # Lookup ones usually have toggleLookupEdit
        if 'Account' in content or 'Brand' in content:
            assert 'toggleLookupEdit' in content, f"toggleLookupEdit missing in {file_path}"


def test_message_detail_view_remains_read_only():
    path = MESSAGE_TEMPLATE_DIR / "messages/detail_view.html"
    assert path.exists(), f"{path} does not exist"

    with path.open("r") as handle:
        content = handle.read()
        assert 'toggleInlineEdit' not in content
        assert 'data-lookup-type' not in content

def test_base_html_has_enable_batch_edit():
    """Verify that base.html defines the enableBatchEdit function."""
    base_path = TEMPLATE_DIR / "base.html"
    with base_path.open("r") as handle:
        content = handle.read()
        assert "function enableBatchEdit()" in content
        assert "document.querySelectorAll('[id^=\"value-\"]').forEach" in content
        assert "document.querySelectorAll('[id^=\"edit-\"]').forEach" in content

def test_base_html_enable_batch_edit_lookup_init():
    """Verify that enableBatchEdit initializes lookups."""
    base_path = TEMPLATE_DIR / "base.html"
    with base_path.open("r") as handle:
        content = handle.read()
        assert "const lookupType = editCont.getAttribute('data-lookup-type')" in content
        assert "const initialId = editCont.getAttribute('data-initial-id')" in content
        assert "const initialName = editCont.getAttribute('data-initial-name')" in content
def test_base_html_cancel_batch_edit_reverts_display():
    """Verify that cancelBatchEdit reverts display style of value elements to empty string."""
    base_path = TEMPLATE_DIR / "base.html"
    with base_path.open("r") as handle:
        content = handle.read()
        assert "document.querySelectorAll('[id^=\"value-\"]').forEach(el => el.style.display = '');" in content
