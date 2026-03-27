from pathlib import Path


LEAD_LIST_VIEW_PATH = "development/web/frontend/templates/leads/list_view.html"
CONTACT_LIST_VIEW_PATH = "development/web/frontend/templates/contacts/list_view.html"


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_lead_list_view_keeps_primary_crud_and_list_view_actions():
    source = _read(LEAD_LIST_VIEW_PATH)

    assert "List View" in source
    assert "window.applyLeadListView(this.value)" in source
    assert "window.toggleLeadListViewPin()" in source
    assert "window.refreshLeadListView()" in source
    assert "Setup" in source
    assert "openModal('/{{ p_type }}/new-modal')" in source
    assert "confirmBulkDelete('{{object_type}}')" in source


def test_lead_list_view_keeps_selection_skeleton_and_row_actions():
    source = _read(LEAD_LIST_VIEW_PATH)

    assert 'id="lead-empty-state"' in source
    assert "No recently viewed leads yet." in source
    assert 'id="gk-list-skeleton"' in source
    assert 'class="sf-table-wrapper"' in source
    assert 'aria-label="Select all records"' in source
    assert "openModal('/leads/{{ item.id }}/convert-modal')" in source
    assert "openModal('{{ item.edit_url }}')" in source
    assert "confirmDelete('{{object_type}}', '{{item.id}}', '{{item.name}}', '{{plural_type}}')" in source


def test_contact_list_view_keeps_shared_list_view_controls_and_empty_state():
    source = _read(CONTACT_LIST_VIEW_PATH)

    assert "window.applyContactListView(this.value)" in source
    assert "window.toggleContactListViewPin()" in source
    assert "window.refreshContactListView()" in source
    assert 'id="contact-empty-state"' in source
    assert "No recently viewed contacts yet." in source
    assert "Customize Contact List View" in source


def test_contact_list_view_keeps_search_selection_and_edit_delete_actions():
    source = _read(CONTACT_LIST_VIEW_PATH)

    assert 'id="contact-list-search"' in source
    assert 'id="contact-list-body"' in source
    assert 'data-record-id="{{ item.id }}"' in source
    assert 'aria-label="Select all records"' in source
    assert "openModal('{{ item.edit_url }}')" in source
    assert "confirmDelete('{{object_type}}', '{{item.id}}', '{{item.name}}', '{{plural_type}}')" in source
