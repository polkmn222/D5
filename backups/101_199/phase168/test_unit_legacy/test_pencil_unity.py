import os
import re
from pathlib import Path

import pytest

TEST_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TEST_DIR.parent.parent
TEMPLATE_DIR = PROJECT_DIR / "frontend" / "templates"
STATIC_DIR = PROJECT_DIR / "frontend" / "static"
DETAIL_FILES = [
    "leads/detail_view.html",
    "contacts/detail_view.html",
    "opportunities/detail_view.html",
    "brands/detail_view.html",
    "models/detail_view.html",
    "products/detail_view.html",
    "assets/detail_view.html",
    "messages/detail_view.html",
    "message_templates/detail_view.html",
    "detail_view.html"
]

@pytest.mark.parametrize("file_path", DETAIL_FILES)
def test_pencil_icon_existence(file_path):
    """Verify that sf-pencil-icon exists in the detail view templates."""
    full_path = TEMPLATE_DIR / file_path
    assert os.path.exists(full_path), f"{full_path} does not exist"
    
    with open(full_path, 'r') as f:
        content = f.read()
        # Basic check for the class name
        assert 'sf-pencil-icon' in content, f"sf-pencil-icon missing in {file_path}"
        # Check for the emoji
        assert '✏️' in content, f"Pencil emoji missing in {file_path}"

@pytest.mark.parametrize("file_path", DETAIL_FILES)
def test_pencil_icon_structure(file_path):
    """Verify that sf-pencil-icon is correctly placed inside sf-editable-field."""
    full_path = TEMPLATE_DIR / file_path
    with open(full_path, 'r') as f:
        content = f.read()
        
        # We use regex because BeautifulSoup might struggle with Jinja2 tags
        # Check for pencil icon inside a div with id starting with value-
        # or inside sf-editable-field
        
        # Check if sf-pencil-icon is within an sf-editable-field
        pattern = r'class="sf-editable-field"[^>]*>.*?sf-pencil-icon.*?</div>'
        match = re.search(pattern, content, re.DOTALL)
        assert match is not None, f"sf-pencil-icon not correctly nested in sf-editable-field in {file_path}"

def test_interactions_css_hides_pencil():
    """Verify that interactions.css has the rule to hide pencil when editing."""
    css_path = STATIC_DIR / "css" / "interactions.css"
    with open(css_path, 'r') as f:
        content = f.read()
        assert '.sf-editing .sf-pencil-icon' in content
        assert 'display: none !important;' in content

def test_base_html_has_editing_class():
    """Verify that base.html adds/removes the sf-editing class."""
    base_path = TEMPLATE_DIR / "base.html"
    with open(base_path, 'r') as f:
        content = f.read()
        assert "document.body.classList.add('sf-editing')" in content
        assert "document.body.classList.remove('sf-editing')" in content

def test_save_batch_edit_handles_multiple_fields():
    """Verify that saveBatchEdit gathers multiple fields."""
    base_path = TEMPLATE_DIR / "base.html"
    with open(base_path, 'r') as f:
        content = f.read()
        # Check for the loop that gathers updates
        assert "document.querySelectorAll('[id^=\"edit-\"]').forEach" in content
        assert "updates[label || fieldId] = input.value" in content

def test_send_message_bulk_delete_ui():
    """Verify that Send Message has the bulk delete UI for templates."""
    path = TEMPLATE_DIR / "send_message.html"
    with open(path, 'r') as f:
        content = f.read()
        assert "template-bulk-delete-modal" in content
        assert "Bulk Del" in content
        assert "template-row-checkbox" in content
        assert "confirmTemplateBulkDelete" in content
