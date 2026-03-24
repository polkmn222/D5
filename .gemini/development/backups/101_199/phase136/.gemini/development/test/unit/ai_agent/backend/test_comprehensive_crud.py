import pytest
import uuid
from sqlalchemy.orm import Session
from unittest.mock import patch, AsyncMock
from pathlib import Path

from db.database import Base, engine, SessionLocal
from ai_agent.backend.service import AiAgentService
from db.models import Lead, Contact, Opportunity, Asset, Product, VehicleSpecification, Model, MessageTemplate

@pytest.fixture
def db():
    # Ensure tables exist in PostgreSQL
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

async def run_crud_test(db, obj_type, create_data, update_data, search_query):
    """Generic helper to test CRUD for any object type."""

    create_prompt = "Create " + obj_type + ": " + " ".join(f"{k} {v}" for k, v in create_data.items())
    
    # 1. CREATE
    mock_create = {
        "intent": "CREATE",
        "object_type": obj_type,
        "data": create_data,
        "text": f"Creating {obj_type}.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_create
        res = await AiAgentService.process_query(db, create_prompt)
        assert "Success" in res["text"]
        
    # Get ID from DB - Filter by deleted_at is None to get the active record
    if obj_type == "brand":
        record = db.query(VehicleSpecification).filter(VehicleSpecification.deleted_at == None).order_by(VehicleSpecification.created_at.desc()).first()
    elif obj_type == "message_template":
        record = db.query(MessageTemplate).filter(MessageTemplate.deleted_at == None).order_by(MessageTemplate.created_at.desc()).first()
    elif obj_type == "lead":
        record = db.query(Lead).filter(Lead.deleted_at == None).order_by(Lead.created_at.desc()).first()
    elif obj_type == "contact":
        record = db.query(Contact).filter(Contact.deleted_at == None).order_by(Contact.created_at.desc()).first()
    elif obj_type == "opportunity":
        record = db.query(Opportunity).filter(Opportunity.deleted_at == None).order_by(Opportunity.created_at.desc()).first()
    elif obj_type == "asset":
        record = db.query(Asset).filter(Asset.deleted_at == None).order_by(Asset.created_at.desc()).first()
    elif obj_type == "product":
        record = db.query(Product).filter(Product.deleted_at == None).order_by(Product.created_at.desc()).first()
    elif obj_type == "model":
        record = db.query(Model).filter(Model.deleted_at == None).order_by(Model.created_at.desc()).first()
    else:
        pytest.fail(f"Unsupported object type in test: {obj_type}")
    
    assert record is not None
    record_id = record.id

    # 2. READ (QUERY)
    mock_query = {
        "intent": "QUERY",
        "object_type": obj_type,
        "sql": f"SELECT * FROM {record.__tablename__} WHERE id = '{record_id}'",
        "text": f"Found {obj_type}.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_query
        res = await AiAgentService.process_query(db, search_query)
        assert len(res["results"]) > 0

    # 3. UPDATE
    mock_update = {
        "intent": "UPDATE",
        "object_type": obj_type,
        "record_id": record_id,
        "data": update_data,
        "text": f"Updating {obj_type}.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_update
        res = await AiAgentService.process_query(db, f"Update {obj_type} {record_id}")
        assert "Success" in res["text"]
        
    # 4. DELETE
    mock_delete = {
        "intent": "DELETE",
        "object_type": obj_type,
        "record_id": record_id,
        "text": f"Deleting {obj_type}.",
        "score": 1.0
    }
    with patch.object(AiAgentService, '_call_multi_llm_ensemble', new_callable=AsyncMock) as mock_ensemble:
        mock_ensemble.return_value = mock_delete
        res = await AiAgentService.process_query(db, f"Delete {obj_type} {record_id}")
        assert "Success" in res["text"]
        
        db.refresh(record)
        assert record.deleted_at is not None

@pytest.mark.asyncio
async def test_all_objects_crud(db):
    # Test cases for each object
    test_cases = [
        ("lead", {"last_name": f"TLead_{uuid.uuid4().hex[:4]}", "status": "New"}, {"status": "Qualified"}, "Show me TestLead"),
        ("contact", {"last_name": f"TCont_{uuid.uuid4().hex[:4]}", "email": "c@test.com"}, {"phone": "123"}, "Find TestContact"),
        ("opportunity", {"name": f"TOpp_{uuid.uuid4().hex[:4]}", "amount": 100}, {"amount": 200}, "Show TestOpp"),
        ("brand", {"name": f"TBrand_{uuid.uuid4().hex[:4]}", "record_type": "Brand"}, {"name": "UpdatedBrand"}, "Search TestBrand"),
        ("model", {"name": f"TModel_{uuid.uuid4().hex[:4]}"}, {"description": "Nice car"}, "Find TestModel"),
        ("product", {"name": f"TProd_{uuid.uuid4().hex[:4]}"}, {"base_price": 500}, "List TestProduct"),
        ("asset", {"vin": f"VIN_{uuid.uuid4().hex[:8]}"}, {"status": "Sold"}, "Show VIN TESTVIN123"),
        ("message_template", {"name": f"TTemp_{uuid.uuid4().hex[:4]}", "content": "Hi"}, {"subject": "Hello"}, "Show TestTemp"),
    ]
    
    for obj_type, c_data, u_data, s_query in test_cases:
        print(f"Testing CRUD for: {obj_type}")
        await run_crud_test(db, obj_type, c_data, u_data, s_query)
