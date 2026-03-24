from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from web.backend.app.api.messaging_router import TemplateCreate, create_template


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.mark.asyncio
async def test_create_template_passes_subject_to_service(db):
    with patch("web.backend.app.api.messaging_router.MessageTemplateService.create_template") as mock_create:
        db.query.return_value.filter.return_value.first.return_value = None
        payload = TemplateCreate(name="Promo", subject="VIP Offer", content="Hello", record_type="SMS")

        await create_template(payload, db)

        _, kwargs = mock_create.call_args
        assert kwargs["subject"] == "VIP Offer"
        assert kwargs["content"] == "Hello"


@pytest.mark.asyncio
async def test_update_template_passes_subject_to_service(db):
    with patch("web.backend.app.api.messaging_router.MessageTemplateService.get_template") as mock_get, \
         patch("web.backend.app.api.messaging_router.MessageTemplateService.update_template") as mock_update:
        mock_get.return_value = MagicMock(id="MT-1")
        payload = TemplateCreate(id="MT-1", name="Promo", subject="Updated Subject", content="Hello again", record_type="LMS")

        await create_template(payload, db)

        _, kwargs = mock_update.call_args
        assert kwargs["subject"] == "Updated Subject"
        assert kwargs["content"] == "Hello again"
