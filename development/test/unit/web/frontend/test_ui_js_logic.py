import os

BASE_HTML_PATH = "development/web/frontend/templates/base.html"
LIST_VIEWS_JS_PATH = "development/web/frontend/static/js/list_views.js"
BULK_ACTION_JS_PATH = "development/web/frontend/static/js/bulk_action.js"
TRASH_TEMPLATE_PATH = "development/web/frontend/templates/trash/list_view.html"

def _read(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

class TestUIJSLogic:
    def test_base_html_search_categorization_exists(self):
        html = _read(BASE_HTML_PATH)
        assert 'const categories = {};' in html
        assert 'categories[item.type].push(item);' in html
        assert 'renderSearchItem(item, itemIdx++, false);' in html

    def test_base_html_search_keyboard_nav_exists(self):
        html = _read(BASE_HTML_PATH)
        assert "e.key === 'ArrowDown'" in html
        assert "searchSelectedIndex = Math.min" in html
        assert "items[searchSelectedIndex].click()" in html

    def test_list_views_js_skeleton_init_exists(self):
        js = _read(LIST_VIEWS_JS_PATH)
        assert 'document.getElementById("gk-list-skeleton")' in js
        assert 'table.closest(".sf-table-wrapper")' in js

    def test_list_views_js_skeleton_visibility_logic_exists(self):
        js = _read(LIST_VIEWS_JS_PATH)
        # Should hide skeleton in updateEmptyState
        assert 'if (listSkeleton) listSkeleton.style.display = "none"' in js
        # Should show skeleton in renderView
        assert 'listSkeleton.style.display = "block"' in js
        # Should hide tableWrapper when loading
        assert 'tableWrapper.style.display = "none"' in js

    def test_list_views_js_render_view_has_delay(self):
        js = _read(LIST_VIEWS_JS_PATH)
        # Verify the 150ms delay for skeleton loader
        assert 'setTimeout(() => {' in js
        assert '}, 150)' in js

    def test_list_views_js_persists_recent_records_and_saved_views(self):
        js = _read(LIST_VIEWS_JS_PATH)
        assert "function readRecentListViewRecords" in js
        assert "function rememberRecentlyViewedRecord" in js
        assert "localStorage.setItem(storageKey, JSON.stringify(records.slice(0, 20)))" in js
        assert "requestLeadListView(url, method, payload)" in js

    def test_bulk_action_js_updates_button_and_calls_shared_endpoint(self):
        js = _read(BULK_ACTION_JS_PATH)
        assert "function toggleAllCheckboxes(source)" in js
        assert "updateDeleteButtonState();" in js
        assert "Delete (${checkboxes.length})" in js
        assert "fetch('/bulk/delete'" in js
        assert "showConfirmModal(title, message, () => {" in js

    def test_trash_template_has_search_windowing_and_load_more_logic(self):
        html = _read(TRASH_TEMPLATE_PATH)
        assert "const trashState = {" in html
        assert "function handleTrashSearch(query)" in html
        assert "function applyTrashFiltersAndWindowing()" in html
        assert "Loading more deleted records..." in html
        assert "document.addEventListener('DOMContentLoaded', () => {" in html
