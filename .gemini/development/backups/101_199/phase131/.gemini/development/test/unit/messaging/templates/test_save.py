import pytest
from unittest.mock import MagicMock, patch, ANY
from fastapi import Request, Form
from sqlalchemy.orm import Session
from web.message.backend.routers.message_template_router import update_template_route
from web.backend.app.api.routers.utility_router import batch_save

@pytest.fixture
def db():
    return MagicMock(spec=Session)

@pytest.fixture
def request_mock():
    req = MagicMock(spec=Request)
    return req

@pytest.mark.asyncio
async def test_update_template_route_content(db):
    template_id = "MT123"
    
    with patch("web.message.backend.services.message_template_service.MessageTemplateService.update_template") as mock_update:
        # 1. Test with 'content'
        print("\nDEBUG: Running test 1 (content)")
        await update_template_route(template_id, name="Test", subject="Sub", content="New Content", record_type="SMS", db=db)
        args, kwargs = mock_update.call_args
        print(f"DEBUG: Test 1 args: {args}, kwargs: {kwargs}")
        assert kwargs["content"] == "New Content"
        assert kwargs["name"] == "Test"
        
        # 2. Test with 'description'
        print("DEBUG: Running test 2 (description)")
        mock_update.reset_mock()
        await update_template_route(template_id, name="Test", subject="Sub", description="Legacy Content", record_type="SMS", db=db)
        args, kwargs = mock_update.call_args
        print(f"DEBUG: Test 2 args: {args}, kwargs: {kwargs}")
        assert kwargs["content"] == "Legacy Content"

        # 3. Test prioritization
        print("DEBUG: Running test 3 (prioritization)")
        mock_update.reset_mock()
        await update_template_route(template_id, name="Test", subject="Sub", content="New", description="Old", record_type="SMS", db=db)
        args, kwargs = mock_update.call_args
        print(f"DEBUG: Test 3 args: {args}, kwargs: {kwargs}")
        assert kwargs["content"] == "New"

@pytest.mark.asyncio
async def test_batch_save_template_content(db, request_mock):
    object_type = "message_templates"
    record_id = "MT123"
    request_mock.json.return_value = {"Content": "Batch Updated Content"}
    
    with patch("web.message.backend.services.message_template_service.MessageTemplateService.get_template") as mock_get, \
         patch("web.message.backend.services.message_template_service.MessageTemplateService.update_template") as mock_update:
        mock_get.return_value = MagicMock()
        await batch_save(object_type, record_id, request_mock, db)
        args, kwargs = mock_update.call_args
        assert kwargs["content"] == "Batch Updated Content"

@pytest.mark.asyncio
async def test_batch_save_template_description_backward_compat(db, request_mock):
    object_type = "message_templates"
    record_id = "MT123"
    request_mock.json.return_value = {"Description": "Legacy Updated Content"}
    
    with patch("web.message.backend.services.message_template_service.MessageTemplateService.get_template") as mock_get, \
         patch("web.message.backend.services.message_template_service.MessageTemplateService.update_template") as mock_update:
        mock_get.return_value = MagicMock()
        await batch_save(object_type, record_id, request_mock, db)
        args, kwargs = mock_update.call_args
        assert kwargs["content"] == "Legacy Updated Content"
