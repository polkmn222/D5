
import pytest
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT / ".gemini/development"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.database import Base, get_db
from db.models import Lead
from ai_agent.ui.backend.service import AiAgentService
from web.backend.app.services.lead_service import LeadService

# Test Database setup (using SQLite for simple integration test if PostgreSQL is not available locally, 
# but the environment says PostgreSQL is mandatory. Let's try to use the actual engine first.)
from db.database import SessionLocal, engine

@pytest.fixture(scope="module")
def db():
    # Use real database for integration test
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestAiAgentLeadIntegration:
    def _run(self, coro):
        import asyncio
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_real_db_lead_create_and_delete(self, db):
        """
        Integration test: 
        1. Create a lead via AiAgentService._execute_intent (bypassing LLM)
        2. Verify it exists in DB.
        3. Delete it via AiAgentService.process_query (testing the bypass logic)
        4. Verify it is deleted in DB.
        """
        conversation_id = "integration_test_177"
        
        # 1. CREATE
        agent_output = {
            "intent": "CREATE",
            "object_type": "lead",
            "data": {
                "first_name": "Integration",
                "last_name": "Tester",
                "email": "integration@test.com",
                "status": "New"
            },
            "language_preference": "eng"
        }
        
        create_response = self._run(AiAgentService._execute_intent(db, agent_output, "create lead", conversation_id=conversation_id))
        
        assert create_response.get("intent") == "OPEN_RECORD"
        record_id = create_response.get("record_id")
        assert record_id is not None
        
        # Verify in DB
        lead_in_db = db.query(Lead).filter(Lead.id == record_id).first()
        assert lead_in_db is not None
        assert lead_in_db.first_name == "Integration"
        
        # 2. DELETE (Explicit ID in query to test Phase 177 bypass)
        delete_query = f"Delete lead {record_id}"
        
        # We need to simulate the context having the object
        from ai_agent.llm.backend.conversation_context import ConversationContextStore
        ConversationContextStore.remember_object(conversation_id, "lead", "QUERY", record_id=record_id)
        
        delete_response = self._run(AiAgentService.process_query(db, delete_query, conversation_id=conversation_id))
        
        # If bypass works, intent should be DELETE
        assert delete_response.get("intent") == "DELETE"
        
        # Verify in DB (soft delete)
        db.expire_all()
        lead_after_delete = db.query(Lead).filter(Lead.id == record_id).first()
        assert lead_after_delete.deleted_at is not None
        
        print(f"\nSUCCESS: Created and deleted lead {record_id} in real DB.")

    def test_real_db_lead_query_schema(self, db):
        """
        Verify that Lead query results contain display_name and model fields.
        """
        user_query = "show all leads"
        agent_output = {
            "intent": "QUERY",
            "object_type": "lead",
            "score": 1.0
        }
        
        response = self._run(AiAgentService._execute_intent(db, agent_output, user_query))
        
        results = response.get("results", [])
        if results:
            first = results[0]
            assert "display_name" in first
            assert "model" in first
            assert "phone" in first
            assert "status" in first
            assert "created_at" in first
            print("\nSUCCESS: Lead table schema aligned with AGENT_TABLE_SCHEMAS.")
        else:
            pytest.skip("No leads in DB to verify schema.")

    def test_real_db_lead_update(self, db):
        """
        Integration test: Update a lead via AiAgentService.
        """
        # Create a lead first
        lead = LeadService.create_lead(db, first_name="Update", last_name="Me", status="New")
        lead_id = lead.id
        
        conversation_id = "integration_test_update"
        
        # Simulate natural language update: "change status to Qualified"
        # Since we bypass LLM, we prepare the agent_output that IntentClassifier would produce
        agent_output = {
            "intent": "UPDATE",
            "object_type": "lead",
            "record_id": lead_id,
            "data": {"status": "Qualified"},
            "language_preference": "eng"
        }
        
        update_response = self._run(AiAgentService._execute_intent(db, agent_output, "update lead", conversation_id=conversation_id))
        
        assert update_response.get("intent") == "OPEN_RECORD"
        
        # Verify in DB
        db.refresh(lead)
        assert lead.status == "Qualified"
        
        print(f"\nSUCCESS: Updated lead {lead_id} status to Qualified in real DB.")

if __name__ == "__main__":
    # If run directly, try to execute tests
    pytest.main([__file__])
