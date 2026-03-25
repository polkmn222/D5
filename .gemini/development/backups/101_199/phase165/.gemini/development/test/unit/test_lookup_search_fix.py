import pytest
from unittest.mock import MagicMock, patch
from backend.app.api.routers.utility_router import lookup_search
from db import models

@pytest.fixture
def db():
    return MagicMock()

@pytest.mark.asyncio
async def test_lookup_search_contact_fix(db):
    # Test that lookup_search for Contact doesn't crash with the new SQL
    q = "test"
    with patch.object(db, "query") as mock_query:
        # Complex chain of calls in SQLAlchemy
        mock_query.return_value.filter.return_value.limit.return_value.all.return_value = []
        
        response = await lookup_search(q, "Contact", db)
        
        assert "results" in response
        assert response["results"] == []
        # Verify that filter was called (implicitly verifying no crash during SQL construction)
        assert mock_query.return_value.filter.called

@pytest.mark.asyncio
async def test_lookup_search_other_types(db):
    for otype in ["Product", "Asset", "Brand", "Model", "Template"]:
        with patch.object(db, "query") as mock_query:
            mock_query.return_value.filter.return_value.limit.return_value.all.return_value = []
            response = await lookup_search("q", otype, db)
            assert "results" in response
