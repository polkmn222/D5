import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock, MagicMock

from db.database import Base
from ai_agent.backend.service import AiAgentService
from db.models import Asset, Product, VehicleSpecification, Model

# Setup Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./db/test_runs/test_ai_agent_auto.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.mark.asyncio
async def test_ai_agent_create_asset_conversational(db):
    """Test that the agent handles asset creation with conversation."""
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
            "vin": "VIN123456789",
            "status": "In Stock"
        },
        "score": 1.0
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_create
        res = await AiAgentService.process_query(db, "VIN번호는 VIN123456789 야")
        assert res["intent"] == "CREATE"
        
        # Verify in DB
        asset = db.query(Asset).filter(Asset.vin == "VIN123456789").first()
        assert asset is not None

@pytest.mark.asyncio
async def test_ai_agent_query_automotive(db):
    """Test that the agent can query brands and products."""
    # Seed a brand
    brand = VehicleSpecification(id="avS-brand-1", name="Tesla", record_type="Brand")
    db.add(brand)
    db.commit()

    mock_llm_query = {
        "intent": "QUERY",
        "object_type": "brand",
        "sql": "SELECT * FROM vehicle_specifications WHERE record_type = 'Brand' AND name LIKE '%Tesla%'",
        "score": 0.95
    }
    
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_llm_query
        res = await AiAgentService.process_query(db, "테슬라 브랜드 찾아줘")
        assert len(res["results"]) > 0
        assert res["results"][0]["name"] == "Tesla"
