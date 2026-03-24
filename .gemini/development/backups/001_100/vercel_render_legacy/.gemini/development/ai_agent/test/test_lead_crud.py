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
from db.models import Lead
from ai_agent.backend.service import AiAgentService

# Test Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestLeadCrudAI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    async def asyncTearDown(self):
        self.db.close()

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_create_lead_ai(self, mock_llm):
        # Mock LLM response for CREATE
        mock_llm.return_value = '{"intent": "CREATE", "object_type": "lead", "data": {"first_name": "Alice", "last_name": "Smith", "email": "alice@example.com"}, "text": "Creating lead..."}'
        
        query = "Create a lead named Alice Smith with email alice@example.com"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "CREATE")
        self.assertIn("Alice Smith", response["text"])
        
        lead = self.db.query(Lead).filter(Lead.email == "alice@example.com").first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.first_name, "Alice")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_query_lead_ai(self, mock_llm):
        # Seed data
        lead = Lead(id="LD-TEST-1", first_name="Bob", last_name="Jones", email="bob@test.com")
        self.db.add(lead)
        self.db.commit()

        # Mock LLM response for QUERY
        mock_llm.return_value = '{"intent": "QUERY", "object_type": "lead", "sql": "SELECT id, first_name, last_name FROM leads WHERE first_name = \'Bob\' AND deleted_at IS NULL", "text": "Searching for Bob..."}'
        
        query = "Find lead named Bob"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "QUERY")
        self.assertTrue(len(response["results"]) > 0)
        self.assertEqual(response["results"][0]["first_name"], "Bob")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_update_lead_ai(self, mock_llm):
        # Seed data
        lead = Lead(id="LD-TEST-2", first_name="Charlie", last_name="Brown", email="charlie@test.com", status="New")
        self.db.add(lead)
        self.db.commit()

        # Mock LLM response for UPDATE
        mock_llm.return_value = '{"intent": "UPDATE", "object_type": "lead", "record_id": "LD-TEST-2", "data": {"status": "Qualified"}, "text": "Updating lead status..."}'
        
        query = "Update lead LD-TEST-2 status to Qualified"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "UPDATE")
        self.assertIn("Success", response["text"])
        
        updated_lead = self.db.query(Lead).filter(Lead.id == "LD-TEST-2").first()
        self.assertEqual(updated_lead.status, "Qualified")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_delete_lead_ai(self, mock_llm):
        # Seed data
        lead = Lead(id="LD-TEST-3", first_name="Daisy", last_name="Miller", email="daisy@test.com")
        self.db.add(lead)
        self.db.commit()

        # Mock LLM response for DELETE
        mock_llm.return_value = '{"intent": "DELETE", "object_type": "lead", "record_id": "LD-TEST-3", "text": "Deleting lead..."}'
        
        query = "Delete lead LD-TEST-3"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "DELETE")
        self.assertIn("Success", response["text"])
        
        deleted_lead = self.db.query(Lead).filter(Lead.id == "LD-TEST-3").first()
        self.assertIsNotNone(deleted_lead.deleted_at)

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_single_word_lead_query(self, mock_llm):
        # Seed data
        lead = Lead(id="LD-TEST-4", first_name="Eve", last_name="Online", email="eve@test.com")
        self.db.add(lead)
        self.db.commit()

        # Mock LLM response with MISSING text and sql (to test fallback)
        mock_llm.return_value = '{"intent": "QUERY", "object_type": "lead"}'
        
        query = "lead"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "QUERY")
        self.assertIn("searched the database", response["text"])
        self.assertTrue(len(response["results"]) > 0)
        self.assertEqual(response["results"][0]["first_name"], "Eve")
        self.assertIn("SELECT", response["sql"])

if __name__ == "__main__":
    unittest.main()
