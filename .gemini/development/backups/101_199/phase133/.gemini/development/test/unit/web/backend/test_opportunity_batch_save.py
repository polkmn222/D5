from unittest.mock import MagicMock, patch

import pytest

from web.backend.app.api.routers.opportunity_router import batch_save_opportunity


@pytest.mark.asyncio
async def test_opportunity_batch_save_rejects_invalid_fields():
    db = MagicMock()
    record = type('OpportunityRecord', (), {'stage': 'Prospecting'})()

    with patch('web.backend.app.api.routers.opportunity_router.OpportunityService.get_opportunity', return_value=record):
        response = await batch_save_opportunity('OPP-1', {'NotARealField': 'x'}, db)

    assert getattr(response, 'status_code', None) == 400


@pytest.mark.asyncio
async def test_opportunity_batch_save_updates_valid_fields():
    db = MagicMock()
    record = type('OpportunityRecord', (), {'stage': 'Prospecting'})()

    with patch('web.backend.app.api.routers.opportunity_router.OpportunityService.get_opportunity', return_value=record), \
         patch('web.backend.app.api.routers.opportunity_router.OpportunityService.update_opportunity', return_value=record) as mock_update:
        response = await batch_save_opportunity('OPP-1', {'Stage': 'Closed Won'}, db)

    assert response == {'status': 'success'}
    mock_update.assert_called_once_with(db, 'OPP-1', stage='Closed Won')
