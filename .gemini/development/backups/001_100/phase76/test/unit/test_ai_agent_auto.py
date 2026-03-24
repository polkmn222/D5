import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

from db.database import Base, engine, SessionLocal
from ai_agent.backend.service import AiAgentService
from db.models import Asset, Product, VehicleSpecification, Model

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.mark.asyncio
async def test_ai_agent_create_asset_conversational(db):
    """Test that the agent handles asset creation with conversation."""
    unique_id = uuid.uuid4().hex[:8]
    test_vin = f"VIN-{unique_id}"

    # 1. User says "I want to register a new car"
    mock_llm_ask = {
        "intent": "CHAT",
        "text": "자동차를 등록하시겠군요! 차량의 VIN(차대번호)을 알려주시겠어요?",
        "score": 0.9
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_ask
        res = await AiAgentService.process_query(db, "새 차 등록하고 싶어")
        assert res["intent"] == "CHAT"
        assert "VIN" in res["text"]

    # 2. User provides VIN
    mock_llm_create = {
        "intent": "CREATE",
        "object_type": "asset",
        "data": {
            "vin": test_vin,
            "status": "In Stock"
        },
        "score": 1.0
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_create
        res = await AiAgentService.process_query(db, f"VIN번호는 {test_vin} 야")
        assert res["intent"] == "CREATE"
        
        # Verify in DB
        asset = db.query(Asset).filter(Asset.vin == test_vin).first()
        assert asset is not None

@pytest.mark.asyncio
async def test_ai_agent_query_automotive(db):
    """Test that the agent can query brands and products."""
    unique_id = uuid.uuid4().hex[:8]
    test_brand_name = f"Tesla-{unique_id}"
    test_brand_id = f"brand-{unique_id}"

    # Seed a brand
    brand = VehicleSpecification(id=test_brand_id, name=test_brand_name, record_type="Brand")
    db.add(brand)
    db.commit()

    mock_llm_query = {
        "intent": "QUERY",
        "object_type": "brand",
        "sql": f"SELECT * FROM vehicle_specifications WHERE record_type = 'Brand' AND name LIKE '%{test_brand_name}%'",
        "score": 0.95
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_query
        res = await AiAgentService.process_query(db, f"{test_brand_name} 브랜드 찾아줘")
        assert len(res["results"]) > 0
        assert res["results"][0]["name"] == test_brand_name
