from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from db.database import get_db
from ai_agent.backend.service import AiAgentService
from ai_agent.backend.conversation_context import ConversationContextStore
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
        selection = body.get("selection")
        
        if not query:
            return {"intent": "CHAT", "text": "Please provide a query."}
        
        page = body.get("page") or 1
        per_page = body.get("per_page") or 50

        response = await AiAgentService.process_query(
            db,
            query,
            conversation_id=conversation_id,
            page=page,
            per_page=per_page,
            selection=selection,
        )
        return response
    except Exception as e:
        return {"intent": "CHAT", "text": f"Error: {str(e)}"}


@router.post("/reset")
@handle_agent_errors
async def reset_agent_session(request: Request) -> Dict[str, Any]:
    body = await request.json()
    conversation_id = body.get("conversation_id")
    ConversationContextStore.clear(conversation_id)
    return {"status": "ok", "conversation_id": conversation_id}
