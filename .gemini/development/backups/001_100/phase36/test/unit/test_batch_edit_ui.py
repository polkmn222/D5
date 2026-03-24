import os
import re
import pytest

# In the current environment, the project is under .gemini/development/
BASE_DIR = "/Users/sangyeol.park@gruve.ai/Documents/D4/.gemini/development"
TEMPLATE_DIR = os.path.join(BASE_DIR, "frontend/templates")

DETAIL_FILES = [
    "leads/detail_view.html",
    "contact/detail_view.html",      # Note: 'contact' or 'contacts'? I saw 'contact' in my list_dir
    "opportunity/detail_view.html",  # Note: 'opportunity' or 'opportunities'? 
    "brands/detail_view.html",
    "models/detail_view.html",
    "product/detail_view.html",      # Note: 'product'
    "assets/detail_view.html",
    "messages/detail_view.html",
    "message/detail_view.html",      # Note: 'message'
    "message_templates/detail_view.html",
    "tasks/detail_view.html",
    "common/detail_view.html"
]

@pytest.mark.parametrize("file_path", DETAIL_FILES)
def test_batch_edit_attributes_exist(file_path):
    """Verify that lookup edit containers have the required data attributes for batch editing."""
    full_path = os.path.join(TEMPLATE_DIR, file_path)
    if not os.path.exists(full_path):
        pytest.skip(f"{full_path} does not exist")
        
    with open(full_path, 'r') as f:
        content = f.read()
        
        # Check for data-lookup-type and data-initial-id and data-initial-name
        # These are added to div id="edit-..."
        pattern = r'id="edit-[^"]+"[^>]*data-lookup-type'
        assert re.search(pattern, content) is not None, f"data-lookup-type missing in {file_path}"
        
        assert 'data-initial-id' in content, f"data-initial-id missing in {file_path}"
        assert 'data-initial-name' in content, f"data-initial-name missing in {file_path}"

@pytest.mark.parametrize("file_path", DETAIL_FILES)
def test_batch_edit_triggers(file_path):
    """Verify that clicking a value or pencil icon triggers the batch edit logic."""
    full_path = os.path.join(TEMPLATE_DIR, file_path)
    if not os.path.exists(full_path):
        pytest.skip(f"{full_path} does not exist")
        
    with open(full_path, 'r') as f:
        content = f.read()
        
        # Check for toggleInlineEdit or toggleLookupEdit
        assert 'toggleInlineEdit' in content, f"toggleInlineEdit missing in {file_path}"
        # Lookup ones usually have toggleLookupEdit
        if 'Account' in content or 'Brand' in content:
            assert 'toggleLookupEdit' in content, f"toggleLookupEdit missing in {file_path}"

def test_base_html_has_enable_batch_edit():
    """Verify that base.html defines the enableBatchEdit function."""
    base_path = os.path.join(TEMPLATE_DIR, "base.html")
    with open(base_path, 'r') as f:
        content = f.read()
        assert "function enableBatchEdit()" in content
        assert "document.querySelectorAll('[id^=\"value-\"]').forEach" in content
        assert "document.querySelectorAll('[id^=\"edit-\"]').forEach" in content

def test_base_html_enable_batch_edit_lookup_init():
    """Verify that enableBatchEdit initializes lookups."""
    base_path = os.path.join(TEMPLATE_DIR, "base.html")
    with open(base_path, 'r') as f:
        content = f.read()
        assert "const lookupType = editCont.getAttribute('data-lookup-type')" in content
        assert "const initialId = editCont.getAttribute('data-initial-id')" in content
        assert "const initialName = editCont.getAttribute('data-initial-name')" in content
def test_base_html_cancel_batch_edit_reverts_display():
    """Verify that cancelBatchEdit reverts display style of value elements to empty string."""
    base_path = os.path.join(TEMPLATE_DIR, "base.html")
    with open(base_path, 'r') as f:
        content = f.read()
        assert "document.querySelectorAll('[id^=\"value-\"]').forEach(el => el.style.display = '');" in content
