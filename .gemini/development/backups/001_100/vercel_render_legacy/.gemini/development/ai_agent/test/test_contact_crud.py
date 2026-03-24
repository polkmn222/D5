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
from db.models import Contact, Lead
from ai_agent.backend.service import AiAgentService

# Test Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_agent_phase3.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestContactCrudAI(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()

    async def asyncTearDown(self):
        self.db.close()

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_create_contact_ai(self, mock_llm):
        # Mock LLM response for CREATE Contact
        mock_llm.return_value = '{"intent": "CREATE", "object_type": "contact", "data": {"first_name": "John", "last_name": "Contact", "email": "john@contact.com"}, "text": "Creating contact..."}'
        
        query = "Create a contact named John Contact with email john@contact.com"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "CREATE")
        self.assertIn("John Contact", response["text"])
        
        contact = self.db.query(Contact).filter(Contact.email == "john@contact.com").first()
        self.assertIsNotNone(contact)
        self.assertEqual(contact.first_name, "John")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_query_contact_ai(self, mock_llm):
        # Seed data
        contact = Contact(id="CT-TEST-1", first_name="Jane", last_name="Doe", email="jane@test.com")
        self.db.add(contact)
        self.db.commit()

        # Mock LLM response for QUERY
        mock_llm.return_value = '{"intent": "QUERY", "object_type": "contact", "sql": "SELECT id, first_name, last_name FROM contacts WHERE first_name = \'Jane\' AND deleted_at IS NULL", "text": "Searching for Jane..."}'
        
        query = "Find contact named Jane"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "QUERY")
        self.assertTrue(len(response["results"]) > 0)
        self.assertEqual(response["results"][0]["first_name"], "Jane")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_update_contact_ai(self, mock_llm):
        # Seed data
        contact = Contact(id="CT-TEST-2", first_name="Bob", last_name="Builder", email="bob@test.com", status="New")
        self.db.add(contact)
        self.db.commit()

        # Mock LLM response for UPDATE
        mock_llm.return_value = '{"intent": "UPDATE", "object_type": "contact", "record_id": "CT-TEST-2", "data": {"status": "Active"}, "text": "Updating contact status..."}'
        
        query = "Update contact CT-TEST-2 status to Active"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "UPDATE")
        self.assertIn("Success", response["text"])
        
        updated_contact = self.db.query(Contact).filter(Contact.id == "CT-TEST-2").first()
        self.assertEqual(updated_contact.status, "Active")

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_delete_contact_ai(self, mock_llm):
        # Seed data
        contact = Contact(id="CT-TEST-3", first_name="Alice", last_name="Wonder", email="alice@test.com")
        self.db.add(contact)
        self.db.commit()

        # Mock LLM response for DELETE
        mock_llm.return_value = '{"intent": "DELETE", "object_type": "contact", "record_id": "CT-TEST-3", "text": "Deleting contact..."}'
        
        query = "Delete contact CT-TEST-3"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "DELETE")
        self.assertIn("Success", response["text"])
        
        deleted_contact = self.db.query(Contact).filter(Contact.id == "CT-TEST-3").first()
        self.assertIsNotNone(deleted_contact.deleted_at)

    @patch("ai_agent.backend.service.AiAgentService._call_llm")
    async def test_recognition_refinement(self, mock_llm):
        # Mock LLM response (though it should be intercepted by code logic)
        mock_llm.return_value = '{"intent": "QUERY", "object_type": "lead", "sql": "SELECT * FROM leads"}'
        
        query = "current created lead"
        response = await AiAgentService.process_query(self.db, query)
        
        self.assertEqual(response["intent"], "CHAT")
        self.assertEqual(response["text"], "I'm here to help with your CRM. What would you like to do?")

if __name__ == "__main__":
    unittest.main()
