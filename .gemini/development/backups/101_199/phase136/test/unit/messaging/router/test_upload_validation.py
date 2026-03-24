from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers
from sqlalchemy.orm import Session

from web.backend.app.services.public_image_storage_service import StoredImage
from web.message.backend.router import upload_template_image, TemplateCreate, create_template, delete_template, _cleanup_template_image
from web.message.backend.routers.message_template_router import template_upload, clear_template_image


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
async def test_upload_template_image_persists_public_storage_result(db):
    file = UploadFile(filename="sample.jpg", file=BytesIO(b"jpg"), headers=Headers({"content-type": "image/jpeg"}))

    with patch(
        "web.message.backend.router.PublicImageStorageService.upload_message_template_image",
        return_value=StoredImage(
            file_path="https://res.cloudinary.com/demo/image/upload/v1/message_templates/sample.jpg",
            provider_key="cloudinary:message_templates/sample",
            storage="cloudinary",
        ),
    ), patch("web.message.backend.router.AttachmentService.create_attachment") as mock_create:
        mock_create.return_value = MagicMock(
            id="ATT-2",
            file_path="https://res.cloudinary.com/demo/image/upload/v1/message_templates/sample.jpg",
            name="sample.jpg",
            file_size=3,
            provider_key="cloudinary:message_templates/sample",
        )

        response = await upload_template_image(file=file, db=db)

        assert isinstance(response, dict)
        assert response["image_url"].startswith("https://res.cloudinary.com/")
        _, kwargs = mock_create.call_args
        assert kwargs["file_path"].startswith("https://res.cloudinary.com/")
        assert kwargs["provider_key"] == "cloudinary:message_templates/sample"


def test_cleanup_template_image_deletes_remote_attachment_asset(db):
    existing = MagicMock(id="MT-remote", attachment_id="ATT-remote", image_url="https://res.cloudinary.com/demo/image/upload/v1/message_templates/old.jpg")
    attachment = MagicMock(
        id="ATT-remote",
        file_path="https://res.cloudinary.com/demo/image/upload/v1/message_templates/old.jpg",
        provider_key="cloudinary:message_templates/old",
    )

    with patch("web.message.backend.router.AttachmentService.get_attachment", return_value=attachment), \
         patch("web.message.backend.router.PublicImageStorageService.delete_image") as mock_delete, \
         patch("web.message.backend.router.AttachmentService.delete") as mock_attachment_delete:
        _cleanup_template_image(db, existing)

        mock_delete.assert_called_once_with(
            file_path="https://res.cloudinary.com/demo/image/upload/v1/message_templates/old.jpg",
            provider_key="cloudinary:message_templates/old",
        )
        mock_attachment_delete.assert_called_once_with(db, "ATT-remote")


@pytest.mark.asyncio
async def test_create_template_passes_image_fields(db):
    with patch("web.message.backend.router.MessageTemplateService.create_template") as mock_create:
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

    with patch("web.message.backend.router.MessageTemplateService.get_template", return_value=existing), \
         patch("web.message.backend.router._cleanup_template_image") as mock_cleanup, \
         patch("web.message.backend.router.MessageTemplateService.update_template") as mock_update:
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

    with patch("web.message.backend.router.MessageTemplateService.get_template", return_value=existing), \
         patch("web.message.backend.router._cleanup_template_image") as mock_cleanup, \
         patch("web.message.backend.router.MessageTemplateService.delete_template") as mock_delete:
        response = await delete_template("MT-3", db)

        assert response == {"status": "success"}
        mock_cleanup.assert_called_once_with(db, existing)
        mock_delete.assert_called_once_with(db, "MT-3")


@pytest.mark.asyncio
async def test_legacy_template_upload_uses_public_storage_service(db):
    template = MagicMock(id="MT-9", attachment_id=None, image_url=None, file_path=None)
    file = UploadFile(filename="detail.jpg", file=BytesIO(b"jpg"), headers=Headers({"content-type": "image/jpeg"}))

    with patch("web.message.backend.routers.message_template_router.MessageTemplateService.get_template", return_value=template), \
         patch(
             "web.message.backend.routers.message_template_router.PublicImageStorageService.upload_message_template_image",
             return_value=StoredImage(
                 file_path="https://res.cloudinary.com/demo/image/upload/v1/message_templates/detail.jpg",
                 provider_key="cloudinary:message_templates/detail",
                 storage="cloudinary",
             ),
         ), \
         patch("web.message.backend.routers.message_template_router.AttachmentService.create_attachment") as mock_create:
        mock_create.return_value = MagicMock(id="ATT-9")

        response = await template_upload("MT-9", file=file, db=db)

        assert isinstance(response, dict)
        assert response["image_url"].startswith("https://res.cloudinary.com/")
        assert template.image_url == response["image_url"]
        assert template.attachment_id == "ATT-9"


@pytest.mark.asyncio
async def test_legacy_clear_image_removes_stored_attachment(db):
    template = MagicMock(
        id="MT-10",
        attachment_id="ATT-10",
        image_url="https://res.cloudinary.com/demo/image/upload/v1/message_templates/detail.jpg",
        file_path="https://res.cloudinary.com/demo/image/upload/v1/message_templates/detail.jpg",
    )
    attachment = MagicMock(
        id="ATT-10",
        file_path="https://res.cloudinary.com/demo/image/upload/v1/message_templates/detail.jpg",
        provider_key="cloudinary:message_templates/detail",
    )

    with patch("web.message.backend.routers.message_template_router.MessageTemplateService.get_template", return_value=template), \
         patch("web.message.backend.routers.message_template_router.AttachmentService.get_attachment", return_value=attachment), \
         patch("web.message.backend.routers.message_template_router.PublicImageStorageService.delete_image") as mock_delete, \
         patch("web.message.backend.routers.message_template_router.AttachmentService.delete") as mock_attachment_delete:
        response = await clear_template_image("MT-10", db)

        assert response == {"status": "success", "message": "Image removed"}
        assert template.image_url == ""
        assert template.file_path == ""
        assert template.attachment_id is None
        mock_delete.assert_called_once_with(
            file_path="https://res.cloudinary.com/demo/image/upload/v1/message_templates/detail.jpg",
            provider_key="cloudinary:message_templates/detail",
        )
        mock_attachment_delete.assert_called_once_with(db, "ATT-10")
