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


@pytest.mark.asyncio
async def test_opportunity_batch_save_maps_lookup_and_named_fields():
    db = MagicMock()
    record = type('OpportunityRecord', (), {'name': 'Current Deal', 'brand': 'brand-1', 'model': 'model-1', 'product': 'product-1', 'contact': 'contact-1', 'asset': 'asset-1'})()

    with patch('web.backend.app.api.routers.opportunity_router.OpportunityService.get_opportunity', return_value=record), \
         patch('web.backend.app.api.routers.opportunity_router.OpportunityService.update_opportunity', return_value=record) as mock_update:
        response = await batch_save_opportunity('OPP-1', {
            'Opportunity Name': 'Harbor Renewal Program',
            'Brand Hidden Ref': 'brand-9',
            'Model Hidden Ref': 'model-9',
            'Product Hidden Ref': 'product-9',
            'Contact Hidden Ref': 'contact-9',
            'Asset Hidden Ref': 'asset-9',
            'Amount': '88,500,000',
            'Probability': '75',
        }, db)

    assert response == {'status': 'success'}
    mock_update.assert_called_once_with(
        db,
        'OPP-1',
        name='Harbor Renewal Program',
        brand='brand-9',
        model='model-9',
        product='product-9',
        contact='contact-9',
        asset='asset-9',
        amount=88500000,
        probability=75,
    )


@pytest.mark.asyncio
async def test_opportunity_batch_save_clears_lookup_fields_to_null():
    db = MagicMock()
    record = type('OpportunityRecord', (), {'asset': 'asset-1'})()

    with patch('web.backend.app.api.routers.opportunity_router.OpportunityService.get_opportunity', return_value=record), \
         patch('web.backend.app.api.routers.opportunity_router.OpportunityService.update_opportunity', return_value=record) as mock_update:
        response = await batch_save_opportunity('OPP-1', {'Asset Hidden Ref': ''}, db)

    assert response == {'status': 'success'}
    mock_update.assert_called_once_with(db, 'OPP-1', asset=None, _force_null_fields=['asset'])
