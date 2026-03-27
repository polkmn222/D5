from pathlib import Path


RELATED_LIST_VIEW_PATH = "development/web/frontend/templates/related/list_view.html"


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_related_list_template_keeps_back_and_optional_new_action_contract():
    source = _read(RELATED_LIST_VIEW_PATH)

    assert "Related List" in source
    assert 'href="{{ back_url }}"' in source
    assert "{% if new_url %}<button class=\"btn btn-primary\" onclick=\"openModal('{{ new_url }}')\">New</button>{% endif %}" in source


def test_related_list_template_keeps_first_column_link_and_optional_actions_column():
    source = _read(RELATED_LIST_VIEW_PATH)

    assert "{% if loop.first and item.get('_href') %}" in source
    assert "class=\"sf-link\"" in source
    assert "{% if show_actions %}<th style=\"width: 120px;\">Actions</th>{% endif %}" in source
    assert "{% if item.get('edit_url') %}<button onclick=\"openModal('{{ item.get('edit_url') }}')\" class=\"btn\" style=\"padding: 2px 8px;\">Edit</button>{% endif %}" in source


def test_related_list_template_keeps_currency_and_empty_rendering_rules():
    source = _read(RELATED_LIST_VIEW_PATH)

    assert "{% if col.lower() in ['amount', 'price', 'base_price'] and cell_value not in [None, ''] %}" in source
    assert "{{ cell_value | currency }}" in source
    assert "{{ cell_value }}" in source
