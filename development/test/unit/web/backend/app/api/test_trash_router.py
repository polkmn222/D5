from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from web.backend.app.api.routers import trash_router


@pytest.mark.asyncio
async def test_trash_list_view_renders_recycle_bin_template(monkeypatch):
    request = MagicMock()
    db = MagicMock()
    captured = {}

    monkeypatch.setattr(
        trash_router.TrashService,
        "list_deleted_records",
        lambda _db: [{"id": "LEAD-1", "name": "Deleted Lead", "type": "Lead"}],
    )

    def fake_template_response(request_obj, template_name, context):
        captured["request"] = request_obj
        captured["template_name"] = template_name
        captured["context"] = context
        return SimpleNamespace(template=SimpleNamespace(name=template_name), context=context)

    monkeypatch.setattr(trash_router.templates, "TemplateResponse", fake_template_response)

    response = await trash_router.trash_list_view(request, db)

    assert response.template.name == "trash/list_view.html"
    assert captured["request"] is request
    assert captured["context"]["page_title"] == "Recycle Bin"
    assert captured["context"]["items"][0]["name"] == "Deleted Lead"


@pytest.mark.asyncio
async def test_trash_list_view_redirects_on_service_error(monkeypatch):
    request = MagicMock()
    db = MagicMock()

    def raise_error(_db):
        raise RuntimeError("boom")

    monkeypatch.setattr(trash_router.TrashService, "list_deleted_records", raise_error)

    response = await trash_router.trash_list_view(request, db)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "/?error=Error+loading+Recycle+Bin"


@pytest.mark.asyncio
async def test_restore_record_endpoint_redirects_with_success_message(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(trash_router.TrashService, "restore_record", lambda *_args, **_kwargs: True)

    response = await trash_router.restore_record_endpoint("Lead", "LEAD-1", db)

    assert response.status_code == 303
    assert response.headers["location"] == "/trash?success=Record+restored+successfully"


@pytest.mark.asyncio
async def test_hard_delete_record_endpoint_redirects_with_error_message_when_delete_fails(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(trash_router.TrashService, "hard_delete_record", lambda *_args, **_kwargs: False)

    response = await trash_router.hard_delete_record_endpoint("Lead", "LEAD-1", db)

    assert response.status_code == 303
    assert response.headers["location"] == "/trash?error=Failed+to+delete+record"
