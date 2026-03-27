from pathlib import Path


TRASH_TEMPLATE_PATH = "development/web/frontend/templates/trash/list_view.html"


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_trash_template_exposes_recycle_bin_search_and_actions():
    source = _read(TRASH_TEMPLATE_PATH)

    assert "Recycle Bin" in source
    assert 'id="trash-summary"' in source
    assert 'placeholder="Search this list..."' in source
    assert 'action="/trash/restore"' in source
    assert "Delete Permanently" in source


def test_trash_template_covers_empty_state_and_load_more_state():
    source = _read(TRASH_TEMPLATE_PATH)

    assert 'id="empty-trash-msg"' in source
    assert "The Recycle Bin is empty." in source
    assert 'id="trash-load-more"' in source
    assert "Loading more deleted records..." in source
    assert "class=\"sf-spinner-small\"" in source


def test_trash_template_keeps_filter_windowing_and_summary_logic():
    source = _read(TRASH_TEMPLATE_PATH)

    assert "displayLimit: 50" in source
    assert "searchTerm: ''" in source
    assert "handleTrashSearch(query)" in source
    assert "applyTrashFiltersAndWindowing()" in source
    assert "Filtered by ${trashState.searchTerm ? 'Search' : 'All Deleted Records'}" in source
    assert "matchCount > trashState.displayLimit" in source


def test_trash_template_keeps_permanent_delete_confirmation_contract():
    source = _read(TRASH_TEMPLATE_PATH)

    assert "function confirmPermanentDelete(objType, id, name)" in source
    assert "'Permanent Delete'" in source
    assert "This action cannot be undone and will delete all related records." in source
    assert "form.action = '/trash/hard-delete';" in source
