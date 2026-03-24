import sys
import os
import asyncio
import unittest
from unittest.mock import patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root and .gemini/skills to path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, ".gemini", "skills"))

from db.database import Base
from db.models import VehicleSpecification, Model
from ai_agent.backend.service import AiAgentService

# Test Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent_phase5.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestBrandModelCrudAI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    async def asyncTearDown(self):
        self.db.close()

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_create_brand_ai(self, mock_llm):
        # Mock LLM response for CREATE Brand
        mock_llm.return_value = '{"intent": "CREATE", "object_type": "brand", "data": {"name": "Test Brand", "description": "High end cars"}, "text": "Creating brand..."}'
        
        query = "Create a brand named Test Brand with description High end cars"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "CREATE")
        self.assertIn("Test Brand", response["text"])
        
        brand = self.db.query(VehicleSpecification).filter(VehicleSpecification.name == "Test Brand").first()
        self.assertIsNotNone(brand)
        self.assertEqual(brand.record_type, "Brand")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_create_model_ai(self, mock_llm):
        # Create a brand first
        brand = VehicleSpecification(id="BR-1", name="Tesla", record_type="Brand")
        self.db.add(brand)
        self.db.commit()

        # Mock LLM response for CREATE Model
        mock_llm.return_value = '{"intent": "CREATE", "object_type": "model", "data": {"name": "Model 3", "brand": "BR-1"}, "text": "Creating model..."}'
        
        query = "Create a model Model 3 for brand BR-1"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "CREATE")
        self.assertIn("Model 3", response["text"])
        
        model = self.db.query(Model).filter(Model.name == "Model 3").first()
        self.assertIsNotNone(model)
        self.assertEqual(model.brand, "BR-1")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_query_brand_ai(self, mock_llm):
        # Seed data
        brand = VehicleSpecification(id="BR-TEST-1", name="Ferrari", record_type="Brand")
        self.db.add(brand)
        self.db.commit()

        # Mock LLM response for QUERY
        mock_llm.return_value = '{"intent": "QUERY", "object_type": "brand", "sql": "SELECT id, name FROM vehicle_specifications WHERE record_type = \'Brand\' AND name = \'Ferrari\' AND deleted_at IS NULL", "text": "Searching for Ferrari..."}'
        
        query = "Show me the Ferrari brand"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "QUERY")
        self.assertTrue(len(response["results"]) > 0)
        self.assertEqual(response["results"][0]["name"], "Ferrari")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_update_model_ai(self, mock_llm):
        # Seed data
        model = Model(id="MOD-TEST-1", name="Civic", description="Old")
        self.db.add(model)
        self.db.commit()

        # Mock LLM response for UPDATE
        mock_llm.return_value = '{"intent": "UPDATE", "object_type": "model", "record_id": "MOD-TEST-1", "data": {"description": "New"}, "text": "Updating model..."}'
        
        query = "Update model MOD-TEST-1 description to New"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "UPDATE")
        self.assertIn("Success", response["text"])
        
        updated_model = self.db.query(Model).filter(Model.id == "MOD-TEST-1").first()
        self.assertEqual(updated_model.description, "New")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_delete_brand_ai(self, mock_llm):
        # Seed data
        brand = VehicleSpecification(id="BR-TEST-DELETE", name="Gone Brand", record_type="Brand")
        self.db.add(brand)
        self.db.commit()

        # Mock LLM response for DELETE
        mock_llm.return_value = '{"intent": "DELETE", "object_type": "brand", "record_id": "BR-TEST-DELETE", "text": "Deleting brand..."}'
        
        query = "Delete brand BR-TEST-DELETE"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "DELETE")
        self.assertIn("Success", response["text"])
        
        deleted_brand = self.db.query(VehicleSpecification).filter(VehicleSpecification.id == "BR-TEST-DELETE").first()
        self.assertIsNotNone(deleted_brand.deleted_at)

if __name__ == "__main__":
    unittest.main()
