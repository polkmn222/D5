from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers
from sqlalchemy.orm import Session

from web.backend.app.api.messaging_router import upload_template_image, TemplateCreate, create_template, delete_template


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.mark.asyncio
async def test_upload_template_image_rejects_non_jpg(db):
    file = UploadFile(filename="sample.png", file=BytesIO(b"png"), headers=Headers({"content-type": "image/png"}))

    response = await upload_template_image(file=file, db=db)

    assert getattr(response, "status_code", None) == 400
    assert "Only JPG images under 500KB are allowed" in bytes(getattr(response, "body", b"")).decode()


@pytest.mark.asyncio
async def test_upload_template_image_rejects_large_file(db):
    content = b"a" * (500 * 1024 + 1)
    file = UploadFile(filename="sample.jpg", file=BytesIO(content), headers=Headers({"content-type": "image/jpeg"}))

    response = await upload_template_image(file=file, db=db)

    assert getattr(response, "status_code", None) == 400
    assert "Only JPG images under 500KB are allowed" in bytes(getattr(response, "body", b"")).decode()


@pytest.mark.asyncio
async def test_create_template_passes_image_fields(db):
    with patch("web.backend.app.api.messaging_router.MessageTemplateService.create_template") as mock_create:
        db.query.return_value.filter.return_value.first.return_value = None
        payload = TemplateCreate(**{
            "name": "MMS Promo",
            "subject": "Sale",
            "content": "Hello",
            "record_type": "MMS",
            "file_path": "/static/uploads/message_templates/file.jpg",
            "attachment_id": "ATT-1",
            "image_url": "/static/uploads/message_templates/file.jpg",
        })

        await create_template(payload, db)

        _, kwargs = mock_create.call_args
        assert kwargs["file_path"] == "/static/uploads/message_templates/file.jpg"
        assert kwargs["attachment_id"] == "ATT-1"
        assert kwargs["image_url"] == "/static/uploads/message_templates/file.jpg"


@pytest.mark.asyncio
async def test_update_template_replaces_old_image_with_cleanup(db):
    existing = MagicMock(id="MT-2", attachment_id="ATT-old", image_url="/static/uploads/message_templates/old.jpg")

    with patch("web.backend.app.api.messaging_router.MessageTemplateService.get_template", return_value=existing), \
         patch("web.backend.app.api.messaging_router._cleanup_template_image") as mock_cleanup, \
         patch("web.backend.app.api.messaging_router.MessageTemplateService.update_template") as mock_update:
        payload = TemplateCreate(**{
            "id": "MT-2",
            "name": "Updated MMS",
            "subject": "Updated",
            "content": "Hello again",
            "record_type": "MMS",
            "file_path": "/static/uploads/message_templates/new.jpg",
            "attachment_id": "ATT-new",
            "image_url": "/static/uploads/message_templates/new.jpg",
        })

        await create_template(payload, db)

        mock_cleanup.assert_called_once_with(db, existing)
        _, kwargs = mock_update.call_args
        assert kwargs["attachment_id"] == "ATT-new"


@pytest.mark.asyncio
async def test_delete_template_cleans_up_existing_image(db):
    existing = MagicMock(id="MT-3", attachment_id="ATT-old", image_url="/static/uploads/message_templates/old.jpg")

    with patch("web.backend.app.api.messaging_router.MessageTemplateService.get_template", return_value=existing), \
         patch("web.backend.app.api.messaging_router._cleanup_template_image") as mock_cleanup, \
         patch("web.backend.app.api.messaging_router.MessageTemplateService.delete_template") as mock_delete:
        response = await delete_template("MT-3", db)

        assert response == {"status": "success"}
        mock_cleanup.assert_called_once_with(db, existing)
        mock_delete.assert_called_once_with(db, "MT-3")
