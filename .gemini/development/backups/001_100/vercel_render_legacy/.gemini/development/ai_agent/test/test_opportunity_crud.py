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
from db.models import Opportunity, Contact
from ai_agent.backend.service import AiAgentService

# Test Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent_phase4.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestOpportunityCrudAI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    async def asyncTearDown(self):
        self.db.close()

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_create_opportunity_ai(self, mock_llm):
        # Mock LLM response for CREATE Opportunity
        mock_llm.return_value = '{"intent": "CREATE", "object_type": "opportunity", "data": {"name": "Big Deal", "contact": "CT-1234", "amount": 50000}, "text": "Creating opportunity..."}'
        
        query = "Create an opportunity named Big Deal for contact CT-1234 with amount 50000"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "CREATE")
        self.assertIn("Big Deal", response["text"])
        
        opp = self.db.query(Opportunity).filter(Opportunity.name == "Big Deal").first()
        self.assertIsNotNone(opp)
        self.assertEqual(opp.amount, 50000)

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_query_opportunity_ai(self, mock_llm):
        # Seed data
        opp = Opportunity(id="OP-TEST-1", name="Test Opp", stage="Qualification", amount=10000)
        self.db.add(opp)
        self.db.commit()

        # Mock LLM response for QUERY
        mock_llm.return_value = '{"intent": "QUERY", "object_type": "opportunity", "sql": "SELECT id, name, stage FROM opportunities WHERE stage = \'Qualification\' AND deleted_at IS NULL", "text": "Searching for opportunities..."}'
        
        query = "Find opportunities in Qualification stage"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "QUERY")
        self.assertTrue(len(response["results"]) > 0)
        self.assertEqual(response["results"][0]["name"], "Test Opp")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_update_opportunity_ai(self, mock_llm):
        # Seed data
        opp = Opportunity(id="OP-TEST-2", name="Old Deal", stage="Prospecting")
        self.db.add(opp)
        self.db.commit()

        # Mock LLM response for UPDATE
        mock_llm.return_value = '{"intent": "UPDATE", "object_type": "opportunity", "record_id": "OP-TEST-2", "data": {"stage": "Closed Won"}, "text": "Updating opportunity stage..."}'
        
        query = "Update opportunity OP-TEST-2 stage to Closed Won"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "UPDATE")
        self.assertIn("Success", response["text"])
        
        updated_opp = self.db.query(Opportunity).filter(Opportunity.id == "OP-TEST-2").first()
        self.assertEqual(updated_opp.stage, "Closed Won")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_delete_opportunity_ai(self, mock_llm):
        # Seed data
        opp = Opportunity(id="OP-TEST-3", name="Dead Deal")
        self.db.add(opp)
        self.db.commit()

        # Mock LLM response for DELETE
        mock_llm.return_value = '{"intent": "DELETE", "object_type": "opportunity", "record_id": "OP-TEST-3", "text": "Deleting opportunity..."}'
        
        query = "Delete opportunity OP-TEST-3"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "DELETE")
        self.assertIn("Success", response["text"])
        
        deleted_opp = self.db.query(Opportunity).filter(Opportunity.id == "OP-TEST-3").first()
        self.assertIsNotNone(deleted_opp.deleted_at)

if __name__ == "__main__":
    unittest.main()
