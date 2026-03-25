import os
import sys
import unittest
import asyncio
from sqlalchemy import create_mock_engine
from sqlalchemy.orm import sessionmaker

# Setup PYTHONPATH mimicking run_crm.sh
# __file__ is /.../.gemini/skills/ai_agent/test/test_interactive_crud.py
# parent 1: test, parent 2: ai_agent, parent 3: skills, parent 4: .gemini, parent 5: D4 (PROJECT_ROOT)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
SKILLS_DIR = os.path.join(PROJECT_ROOT, ".gemini", "skills")

sys.path.append(PROJECT_ROOT)
sys.path.append(SKILLS_DIR)

from db.database import SessionLocal, get_db
from ai_agent.backend.service import AiAgentService
from db.models import Lead

class TestInteractiveCRUD(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = SessionLocal()
        # Find a test lead
        self.test_lead = self.db.query(Lead).filter(Lead.deleted_at == None).first()
        if not self.test_lead:
            # Create a dummy lead if none exist
            self.test_lead = Lead(id="LD-TEST-123", first_name="Test", last_name="Interactive", status="New")
            self.db.add(self.test_lead)
            self.db.commit()
            self.db.refresh(self.test_lead)

    def tearDown(self):
        self.db.close()

    async def test_manage_lead_selection(self):
        """Test that sending 'Manage lead [ID]' returns the correct interactive prompt."""
        query = f"Manage lead {self.test_lead.id}"
        response = await AiAgentService.process_query(self.db, query)
        
        print(f"\n[TEST] Query: {query}")
        print(f"[TEST] Response: {response.get('text')}")
        
        self.assertEqual(response.get("intent"), "MANAGE")
        self.assertIn(self.test_lead.id, response.get("text"))
        self.assertIn("What would you like to do?", response.get("text"))

    async def test_update_via_interaction(self):
        """Test that updating a field after selection works."""
        # Simulate the user providing a new status for the selected lead
        query = f"Update status to Qualified for lead {self.test_lead.id}"
        response = await AiAgentService.process_query(self.db, query)
        
        print(f"\n[TEST] Query: {query}")
        print(f"[TEST] Response: {response.get('text')}")
        
        # Verify DB change
        self.db.refresh(self.test_lead)
        self.assertEqual(self.test_lead.status, "Qualified")
        self.assertEqual(response.get("intent"), "UPDATE")
        self.assertIn("Success", response.get("text"))

if __name__ == "__main__":
    unittest.main()
