import os

BASE_CSS_PATH = "development/web/frontend/static/css/base.css"
LIST_VIEWS_CSS_PATH = "development/web/frontend/static/css/list_views.css"
BASE_HTML_PATH = "development/web/frontend/templates/base.html"
LIST_VIEW_FILES = [
    "development/web/frontend/templates/leads/list_view.html",
    "development/web/frontend/templates/contacts/list_view.html",
    "development/web/frontend/templates/opportunities/list_view.html",
    "development/web/frontend/templates/models/list_view.html",
    "development/web/frontend/templates/products/list_view.html",
    "development/web/frontend/templates/assets/list_view.html",
    "development/web/frontend/templates/brands/list_view.html",
    "development/web/frontend/templates/vehicle_spec/list_view.html",
    "development/web/frontend/templates/message/list_view.html",
    "development/web/frontend/templates/list_view.html",
]
JS_LIST_VIEWS_PATH = "development/web/frontend/static/js/list_views.js"
RELATED_LIST_VIEW_PATH = "development/web/frontend/templates/related/list_view.html"
TRASH_LIST_VIEW_PATH = "development/web/frontend/templates/trash/list_view.html"

def _read(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

class TestGKDesignSystem:
    def test_base_css_has_gk_variables(self):
        css = _read(BASE_CSS_PATH)
        assert "--radius: 0.5rem" in css
        assert "--shadow: 0 4px 6px -1px" in css
        assert "--transition: all 0.2s" in css

    def test_list_views_has_responsive_table_rules(self):
        css = _read(LIST_VIEWS_CSS_PATH)
        assert "overflow-x: auto" in css
        assert "position: sticky" in css

    def test_list_view_html_files_updated(self):
        for path in LIST_VIEW_FILES:
            html = _read(path)
            assert 'gk-list-skeleton' in html
            assert 'sf-table-wrapper' in html
            assert 'role="grid"' in html
            assert 'aria-label="Select all records"' in html

    def test_base_html_has_accessibility_updates(self):
        html = _read(BASE_HTML_PATH)
        assert 'aria-label="Global search"' in html
        assert 'role="listbox"' in html

    def test_js_list_views_has_propagation_fix(self):
        js = _read(JS_LIST_VIEWS_PATH)
        assert 'event.stopPropagation(); window.${removeFilterFunctionName}(this)' in js

    def test_related_list_template_keeps_back_new_and_linked_first_column_contract(self):
        html = _read(RELATED_LIST_VIEW_PATH)
        assert "Related List" in html
        assert 'href="{{ back_url }}"' in html
        assert "openModal('{{ new_url }}')" in html
        assert "class=\"sf-link\"" in html
        assert "{% if show_actions %}<th style=\"width: 120px;\">Actions</th>{% endif %}" in html

    def test_trash_list_template_has_empty_and_loading_states(self):
        html = _read(TRASH_LIST_VIEW_PATH)
        assert "Recycle Bin" in html
        assert "The Recycle Bin is empty." in html
        assert "id=\"trash-load-more\"" in html
        assert "class=\"sf-spinner-small\"" in html
        assert "confirmPermanentDelete" in html
