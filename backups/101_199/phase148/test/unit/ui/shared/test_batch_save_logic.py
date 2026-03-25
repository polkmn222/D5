import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request
from sqlalchemy.orm import Session
from web.backend.app.api.routers.utility_router import batch_save
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.opportunity_service import OpportunityService

@pytest.fixture
def db():
    return MagicMock(spec=Session)

@pytest.fixture
def request_mock():
    req = MagicMock(spec=Request)
    return req

@pytest.mark.asyncio
async def test_batch_save_lead_name_split(db, request_mock):
    # Setup
    object_type = "leads"
    record_id = "LEAD123"
    request_mock.json.return_value = {"Name": "John Doe", "Status": "Qualified"}
    
    with patch("web.backend.app.services.lead_service.LeadService.get_lead") as mock_get, \
         patch("web.backend.app.services.lead_service.LeadService.update_lead") as mock_update:
        
        mock_get.return_value = MagicMock()
        
        # Execute
        response = await batch_save(object_type, record_id, request_mock, db)
        
        # Verify
        assert response == {"status": "success"}
        mock_update.assert_called_once_with(
            db, record_id, first_name="John", last_name="Doe", status="Qualified"
        )

@pytest.mark.asyncio
async def test_batch_save_opportunity_fields(db, request_mock):
    # Setup
    object_type = "opportunities"
    record_id = "OPP456"
    request_mock.json.return_value = {
        "Opportunity Name": "Big Deal",
        "Amount": "1,000,000",
        "Stage": "Closed Won",
        "brand_hidden_ref": "brand_id"
    }
    
    with patch("web.backend.app.services.opportunity_service.OpportunityService.get_opportunity") as mock_get, \
         patch("web.backend.app.services.opportunity_service.OpportunityService.update_opportunity") as mock_update:
        
        mock_get.return_value = MagicMock()
        
        # Execute
        response = await batch_save(object_type, record_id, request_mock, db)
        
        # Verify
        assert response == {"status": "success"}
        mock_update.assert_called_once_with(
            db, record_id, name="Big Deal", amount="1000000", stage="Closed Won", brand="brand_id"
        )


@pytest.mark.asyncio
async def test_batch_save_supports_message_records(db, request_mock):
    object_type = "messages"
    record_id = "MSG123"
    request_mock.json.return_value = {
        "Status": "Delivered",
        "Template Hidden Ref": "TPL001",
    }

    with patch("web.message.backend.services.message_service.MessageService.get_message") as mock_get, \
         patch("web.message.backend.services.message_service.MessageService.update_message") as mock_update:

        mock_get.return_value = MagicMock(status="Sent", template="TPL000")

        response = await batch_save(object_type, record_id, request_mock, db)

        assert response == {"status": "success"}
        mock_update.assert_called_once_with(db, record_id, status="Delivered", template="TPL001")


@pytest.mark.asyncio
async def test_batch_save_clears_lookup_fields_with_force_null(db, request_mock):
    object_type = "models"
    record_id = "MOD123"
    request_mock.json.return_value = {
        "Brand Hidden Ref": "",
    }

    with patch("web.backend.app.services.model_service.ModelService.get_model") as mock_get, \
         patch("web.backend.app.services.model_service.ModelService.update_model") as mock_update:

        mock_get.return_value = MagicMock(brand="BRAND1")

        response = await batch_save(object_type, record_id, request_mock, db)

        assert response == {"status": "success"}
        mock_update.assert_called_once_with(db, record_id, brand=None, _force_null_fields=['brand'])

@pytest.mark.asyncio
async def test_batch_save_invalid_json(db, request_mock):
    from fastapi.responses import JSONResponse
    request_mock.json.side_effect = Exception("Invalid JSON")
    response = await batch_save("leads", "123", request_mock, db)
    assert isinstance(response, JSONResponse)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_batch_save_unsupported_object(db, request_mock):
    response = await batch_save("unsupported", "123", request_mock, db)
    # This one might return a JSONResponse too now
    from fastapi.responses import JSONResponse
    if isinstance(response, JSONResponse):
        assert response.status_code == 404
    else:
        assert response == {"status": "error", "message": "Object type not supported"}
