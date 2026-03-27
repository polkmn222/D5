from pathlib import Path


LEAD_DETAIL_VIEW_PATH = "development/web/frontend/templates/leads/detail_view.html"
CONTACT_DETAIL_VIEW_PATH = "development/web/frontend/templates/contacts/detail_view.html"


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_lead_detail_view_keeps_open_edit_delete_and_conversion_actions():
    source = _read(LEAD_DETAIL_VIEW_PATH)

    assert "Details" in source
    assert "Related" in source
    assert "openModal('/leads/{{ record_id }}/convert')" in source
    assert "openModal('/{{ plural_type }}/new-modal?id={{ record_id }}')" in source
    assert "confirmDelete('{{object_type}}', '{{record_id}}', '{{record_name}}', '{{plural_type}}')" in source


def test_lead_detail_view_keeps_inline_edit_and_related_empty_state_contract():
    source = _read(LEAD_DETAIL_VIEW_PATH)

    assert "toggleInlineEdit('{{ field }}', '{{ plural_type }}', '{{ record_id }}', '{{ field }}')" in source
    assert "toggleLookupEdit('{{ field }}'" in source
    assert "shared/detail_system_info.html" in source
    assert "No related records found." in source
    assert "View All" in source


def test_contact_detail_view_keeps_detail_tabs_and_object_level_actions():
    source = _read(CONTACT_DETAIL_VIEW_PATH)

    assert "Details" in source
    assert "Related" in source
    assert "openModal('/{{ plural_type }}/new-modal?id={{ record_id }}')" in source
    assert "confirmDelete('{{object_type}}', '{{record_id}}', '{{record_name}}', '{{plural_type}}')" in source
    assert "toggleInlineEdit('{{ field }}', '{{ plural_type }}', '{{ record_id }}', '{{ field }}')" in source


def test_contact_detail_view_keeps_related_card_new_and_view_all_actions():
    source = _read(CONTACT_DETAIL_VIEW_PATH)

    assert "Connected records for this contact, similar to Salesforce related lists." in source
    assert "{% if list.new_url %}<button class=\"btn btn-primary\" onclick=\"openModal('{{ list.new_url }}')\">New</button>{% endif %}" in source
    assert "{% if list.view_all_url %}<a class=\"btn\" style=\"text-decoration: none; color: var(--text);\" href=\"{{ list.view_all_url }}\">View All</a>{% endif %}" in source
    assert "No related records found." in source
