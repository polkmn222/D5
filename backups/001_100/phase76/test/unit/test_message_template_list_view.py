import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from sqlalchemy.orm import Session
from web.backend.app.api.routers.message_template_router import list_templates

@pytest.fixture
def db():
    return MagicMock(spec=Session)

@pytest.fixture
def request_mock():
    req = MagicMock(spec=Request)
    # Mocking templates.TemplateResponse properly is complex, 
    # so we'll patch the templates object instead
    return req

@pytest.mark.asyncio
async def test_list_templates_includes_content(db, request_mock):
    # Setup
    mock_template = MagicMock()
    mock_template.id = "MT1"
    mock_template.name = "Test Template"
    mock_template.subject = "Test Subject"
    mock_template.content = "Test Content Body"
    mock_template.record_type = "SMS"
    
    with patch("web.backend.app.services.message_template_service.MessageTemplateService.get_templates") as mock_get, \
         patch("web.backend.app.api.routers.message_template_router.templates.TemplateResponse") as mock_render:
        
        mock_get.return_value = [mock_template]
        
        # Execute
        await list_templates(request_mock, db)
        
        # Verify
        assert mock_render.called
        args, kwargs = mock_render.call_args
        context = args[2]
        
        assert "items" in context
        assert "columns" in context
        assert "content" in context["columns"]
        
        # Check that the item has the content field
        item = context["items"][0]
        assert item["content"] == "Test Content Body"
        assert context["plural_type"] == "message_templates"
