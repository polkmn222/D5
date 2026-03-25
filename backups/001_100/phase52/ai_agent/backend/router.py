from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from db.database import get_db
from ai_agent.backend.service import AiAgentService
from backend.app.utils.error_handler import handle_agent_errors

router = APIRouter(prefix="/api", tags=["AI Agent"])

@router.post("/chat")
@handle_agent_errors
async def chat_with_agent(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Endpoint for natural language chat with the AI Agent.
    """
    try:
        body = await request.json()
        query = body.get("query")
        conversation_id = body.get("conversation_id")
        
        if not query:
            return {"intent": "CHAT", "text": "Please provide a query."}
        
        response = await AiAgentService.process_query(db, query, conversation_id=conversation_id)
        return response
    except Exception as e:
        return {"intent": "CHAT", "text": f"Error: {str(e)}"}
