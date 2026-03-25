import os
import json
import httpx
import logging
import re
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Import services from the main app
from backend.app.services.lead_service import LeadService
from backend.app.services.contact_service import ContactService
from backend.app.services.opportunity_service import OpportunityService
from backend.app.services.vehicle_spec_service import VehicleSpecService
from backend.app.services.model_service import ModelService
from backend.app.services.message_template_service import MessageTemplateService
from backend.app.services.message_service import MessageService
from backend.app.utils.error_handler import handle_agent_errors
from .recommendations import AIRecommendationService
from .intent_preclassifier import IntentPreClassifier
from .conversation_context import ConversationContextStore
from .intent_reasoner import IntentReasoner

load_dotenv()

logger = logging.getLogger(__name__)

# API Keys from .env
CEREBRAS_API_KEY = os.getenv("CELEBRACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_API_Key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("ChatGPT_API_Key")

# Skills directory is 3 levels up from this file
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_PATH = os.path.join(SKILLS_DIR, "backend", "metadata.json")

class AiAgentService:
    @staticmethod
    def _get_metadata() -> str:
        try:
            # Check for multiple possible metadata paths due to reorganization
            paths_to_check = [
                METADATA_PATH,
                os.path.join(os.getcwd(), "backend", "metadata.json"),
                os.path.join(os.getcwd(), ".gemini", "development", "backend", "metadata.json")
            ]
            for p in paths_to_check:
                if os.path.exists(p):
                    with open(p, "r") as f:
                        return json.dumps(json.load(f), indent=2)
            return "{}"
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return "{}"

    @staticmethod
    def _sanitize_pagination(page: Optional[int], per_page: Optional[int]) -> tuple[int, int, int]:
        safe_page = max(int(page or 1), 1)
        safe_per_page = max(1, min(int(per_page or 50), 50))
        offset = (safe_page - 1) * safe_per_page
        return safe_page, safe_per_page, offset

    @staticmethod
    def _default_query_parts(obj: str) -> Optional[Dict[str, str]]:
        mapping = {
            "lead": {
                "select": "id, first_name, last_name, email, phone, status",
                "from": "leads",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "contact": {
                "select": "id, first_name, last_name, email, phone, status",
                "from": "contacts",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "opportunity": {
                "select": "id, name, stage, amount, status",
                "from": "opportunities",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "brand": {
                "select": "id, name, record_type, description",
                "from": "vehicle_specifications",
                "where": "record_type = 'Brand' AND deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "model": {
                "select": "id, name, brand, description",
                "from": "models",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "product": {
                "select": "id, name, brand, model, category, base_price",
                "from": "products",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "asset": {
                "select": "id, vin, brand, model, status",
                "from": "assets",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "message_template": {
                "select": "id, name, subject, content, record_type, image_url, attachment_id, file_path",
                "from": "message_templates",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "message_send": {
                "select": "id, contact, template, direction, status, sent_at",
                "from": "message_sends",
                "where": "deleted_at IS NULL",
                "order_by": "sent_at DESC",
            },
        }
        return mapping.get(obj)

    @classmethod
    def _execute_paginated_query(
        cls,
        db: Session,
        sql: str,
        obj: str,
        page: int,
        per_page: int,
    ) -> Dict[str, Any]:
        safe_page, safe_per_page, offset = cls._sanitize_pagination(page, per_page)
        clean_sql = sql.strip().rstrip(";")

        count_result = db.execute(text(f"SELECT COUNT(*) AS total_count FROM ({clean_sql}) AS agent_query_count"))
        total = int(count_result.scalar() or 0)
        paged_sql = f"SELECT * FROM ({clean_sql}) AS agent_query_page LIMIT {safe_per_page} OFFSET {offset}"
        result = db.execute(text(paged_sql))
        total_pages = max(1, (total + safe_per_page - 1) // safe_per_page)

        return {
            "results": [dict(row._mapping) for row in result],
            "sql": paged_sql,
            "pagination": {
                "page": safe_page,
                "per_page": safe_per_page,
                "total": total,
                "total_pages": total_pages,
                "object_type": obj,
            },
        }

    @classmethod
    def _resolve_contextual_record_reference(cls, user_query: str, conversation_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not conversation_id:
            return None

        context = ConversationContextStore.get_context(conversation_id)
        last_created = context.get("last_created") or {}
        object_type = context.get("last_object") or last_created.get("object_type")
        record_id = context.get("last_record_id") or last_created.get("record_id")

        if not object_type or not record_id:
            return None

        q_low = user_query.lower()
        recent_markers = ["just created", "recently created", "방금 생성", "방금 만든"]
        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        if explicit_objects and object_type not in explicit_objects:
            return None

        if any(marker in q_low or marker in user_query for marker in recent_markers):
            return {
                "intent": "MANAGE",
                "object_type": object_type,
                "record_id": record_id,
                "score": 1.0,
            }

        follow_up_markers = ["that", "this", "it", "record", "그", "이", "해당", "방금", "최근"]
        has_follow_up_marker = any(marker in q_low or marker in user_query for marker in follow_up_markers)
        manage_markers = ["show", "open", "manage", "view", "details", "보여", "열어", "관리", "상세"]
        update_markers = ["update", "edit", "change", "modify", "수정", "변경", "바꿔"]

        if has_follow_up_marker and any(marker in q_low or marker in user_query for marker in manage_markers + update_markers):
            return {
                "intent": "MANAGE",
                "object_type": object_type,
                "record_id": record_id,
                "score": 1.0,
            }
        
        return None

    @classmethod
    def _resolve_delete_confirmation(cls, user_query: str, conversation_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not conversation_id:
            return None

        q_low = user_query.lower()
        pending_delete = ConversationContextStore.get_pending_delete(conversation_id)
        if pending_delete:
            if any(token in q_low for token in ["yes", "confirm", "proceed", "delete it", "yes delete"]):
                ConversationContextStore.clear_pending_delete(conversation_id)
                return {
                    "intent": "DELETE",
                    "object_type": pending_delete.get("object_type"),
                    "record_id": pending_delete.get("record_id"),
                    "score": 1.0,
                }
            if any(token in q_low for token in ["cancel", "stop", "no", "never mind"]):
                ConversationContextStore.clear_pending_delete(conversation_id)
                return {
                    "intent": "CHAT",
                    "text": "Delete request cancelled.",
                    "score": 1.0,
                }

        normalized_query = IntentPreClassifier.normalize(user_query)
        delete_markers = ["delete", "remove", "erase", "삭제"]
        if not any(marker in q_low or marker in user_query for marker in delete_markers):
            return None

        object_type = None
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        if explicit_objects:
            object_type = explicit_objects[0]

        context = ConversationContextStore.get_context(conversation_id)
        if not object_type:
            object_type = context.get("last_object")

        record_id = context.get("last_record_id")
        last_created = context.get("last_created") or {}
        if not record_id:
            record_id = last_created.get("record_id")
        if not object_type:
            object_type = last_created.get("object_type")

        if explicit_objects and object_type and object_type not in explicit_objects:
            return None
        if not object_type or not record_id:
            return None

        ConversationContextStore.remember_pending_delete(conversation_id, object_type, record_id)
        label = object_type.replace("_", " ")
        return {
            "intent": "CHAT",
            "object_type": object_type,
            "record_id": record_id,
            "text": f"Delete confirmation needed: should I permanently delete this {label} record ({record_id})? Reply 'yes' to continue or 'cancel' to keep it.",
            "score": 1.0,
        }

    @classmethod
    def _resolve_send_message_request(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        selection: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        q_low = user_query.lower()
        send_markers = ["send message", "send messages", "message them", "text them", "메시지 보내"]
        if not any(marker in q_low or marker in user_query for marker in send_markers):
            return None

        selection_payload = selection or ConversationContextStore.get_selection(conversation_id)
        object_type = (selection_payload or {}).get("object_type")
        ids = (selection_payload or {}).get("ids") or []
        context = ConversationContextStore.get_context(conversation_id)

        template_id = None
        if context.get("last_object") in ["message_template", "template"] and context.get("last_record_id"):
            template_id = context.get("last_record_id")
        last_created = context.get("last_created") or {}
        if not template_id and last_created.get("object_type") == "message_template":
            template_id = last_created.get("record_id")

        if not object_type or not ids:
            return {
                "intent": "CHAT",
                "text": "Select one or more records first, then ask me to send a message.",
                "score": 1.0,
            }

        return {
            "intent": "SEND_MESSAGE",
            "object_type": object_type,
            "selection": {"object_type": object_type, "ids": ids},
            "template_id": template_id,
            "redirect_url": f"/send?sourceObject={object_type}&count={len(ids)}",
            "text": f"Opening the messaging flow for {len(ids)} selected {object_type} record(s).",
            "score": 1.0,
        }

    @classmethod
    async def process_query(
        cls,
        db: Session,
        user_query: str,
        conversation_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        selection: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ConversationContextStore.remember_selection(conversation_id, selection)

        send_message_resolution = cls._resolve_send_message_request(user_query, conversation_id, selection)
        if send_message_resolution:
            return await cls._execute_intent(
                db,
                send_message_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        delete_resolution = cls._resolve_delete_confirmation(user_query, conversation_id)
        if delete_resolution:
            return await cls._execute_intent(db, delete_resolution, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        contextual_response = cls._resolve_contextual_record_reference(user_query, conversation_id)
        if contextual_response:
            return await cls._execute_intent(db, contextual_response, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        clarification = IntentReasoner.clarify_if_needed(user_query)
        if clarification:
            return clarification

        # ---- Phase 49: Hybrid Intent Pre-Classification ----
        rule_based = IntentPreClassifier.detect(user_query)
        if rule_based:
            return await cls._execute_intent(db, rule_based, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        metadata = cls._get_metadata()
        
        system_prompt = f"""
        You are the "AI Agent" for an Automotive CRM (D4). 
        DATABASE SCHEMA:
        {metadata}
        
        OBJECTIVE:
        Operate all functions in D4 based on natural language or interactive requests.
        Only provide answers based on D4 information.
        Support both English and Korean languages natively. Detect user language and respond in the same language.
        
        CONVERSATIONAL CONTEXT:
        - You must remember the previous turn's intent. 
        - If a user provides a single word (e.g., "New", "박상열") in response to your question, interpret it within the context of the previous request.
        - For Korean names like "박상열", map it to `last_name` (mandatory) if you only have one name string.
        
        CONVERSATIONAL CREATE FLOW:
        - If a user wants to CREATE a record (lead, contact, opportunity, brand, model, product, asset, template) but hasn't provided mandatory info:
          1. Use intent "CHAT".
          2. Acknowledge the request.
          3. Politely ask for missing info.
             - Lead/Contact: needs at least "last_name" and "status".
             - Asset: needs "vin".
             - Template: needs "name" and "content".
          4. Do NOT use intent "CREATE" until you have the mandatory fields.
        
        QUERY FLOW:
        - When searching for "recent" or "just created" records, generate a SQL with `ORDER BY created_at DESC LIMIT 1`.
        - Always filter by `deleted_at IS NULL`.
        - Mapping: "messages" should query the `message_sends` table.
        - Attachments: These are system-internal files. Do NOT list them unless explicitly asked about files linked to a specific record.
        
        INTERACTIVE MANAGE FLOW:
        - When you receive "Manage [ObjectType] [RecordID]":
          1. Use intent "MANAGE".
          2. Describe the record.
          3. List available fields using bracket format (e.g., "[First Name]", "[Status]").
          4. Ask for the next action.
        
        RESPONSE FORMAT (Strict JSON):
        {{
            "intent": "QUERY" | "CREATE" | "UPDATE" | "DELETE" | "MANAGE" | "CHAT" | "RECOMMEND" | "MODIFY_UI",
            "text": "Helpful response here",
            "sql": "SELECT ... (if QUERY)",
            "data": {{ "field": "value" }} (if CREATE/UPDATE),
            "object_type": "lead" | "contact" | "opportunity" | "brand" | "model" | "product" | "asset" | "message_template" | "message_send",
            "record_id": "ID_HERE",
            "score": 0.0 to 1.0 (confidence in this JSON)
        }}
        """

        # Call Multi-LLM Ensemble
        agent_output = await cls._call_multi_llm_ensemble(user_query, system_prompt)
        
        # MANUAL OVERRIDE: Check for specific keyword triggers
        q_low = user_query.lower()
        
        # Priority 1: Specific Mode Selections (MODIFY_UI) - Check specific strings
        if "hot deals" in q_low or "high value" in q_low or "closing soon" in q_low:
             agent_output["intent"] = "MODIFY_UI"
        
        # Priority 2: Generic Change Logic Request (MODIFY_UI)
        elif "change" in q_low and ("ai recommend" in q_low or "추천" in q_low or "logic" in q_low):
             agent_output["intent"] = "MODIFY_UI"
        
        # Priority 3: Style changes (MODIFY_UI)
        elif any(word in q_low for word in ["table format", "테이블 형식", "테이블 모양", "compact style", "modern style", "default style"]):
             agent_output["intent"] = "MODIFY_UI"

        # Priority 3: Actual Recommendation request
        elif ("ai recommend" in q_low or "추천" in q_low) and "change" not in q_low:
            agent_output["intent"] = "RECOMMEND"
        elif "send message" in q_low or "메시지 보내" in q_low:
             agent_output["intent"] = "SEND_MESSAGE"
             agent_output["text"] = "Redirecting you to the messaging page..."
        elif "usage" in q_low or "사용량" in q_low or "토큰" in q_low:
             agent_output["intent"] = "USAGE"

        # ROBUST EXTRACTION: Fallback for "Manage [object] [record_id]"
        if "manage" in user_query.lower() and (not agent_output.get("record_id") or agent_output.get("record_id") == "ID_HERE"):
            match = re.search(r"manage\s+(\w+)\s+([\w-]+)", user_query, re.IGNORECASE)
            if match:
                agent_output["intent"] = "MANAGE"
                agent_output["object_type"] = match.group(1).lower()
                agent_output["record_id"] = match.group(2)

        try:
            return await cls._execute_intent(db, agent_output, user_query, conversation_id=conversation_id, page=page, per_page=per_page)
        except Exception as e:
            logger.error(f"Execution Error: {str(e)}")
            return {"intent": "CHAT", "text": f"Technical issue: {str(e)}"}

    @classmethod
    async def _call_multi_llm_ensemble(cls, user_query: str, system_prompt: str) -> Dict[str, Any]:
        """Calls multiple LLMs in parallel and picks the best response based on a score."""
        tasks = []
        
        if CEREBRAS_API_KEY:
            tasks.append(cls._call_cerebras(user_query, system_prompt))
        if GROQ_API_KEY:
            tasks.append(cls._call_groq(user_query, system_prompt))
        if GEMINI_API_KEY:
            tasks.append(cls._call_gemini(user_query, system_prompt))
        if OPENAI_API_KEY:
            tasks.append(cls._call_openai(user_query, system_prompt))

        if not tasks:
            return {"intent": "CHAT", "text": "No AI API Keys configured."}

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_responses = []
        for res in responses:
            if isinstance(res, dict) and "intent" in res:
                valid_responses.append(res)
            elif isinstance(res, Exception):
                logger.error(f"Ensemble member failed: {res}")

        if not valid_responses:
            return {"intent": "CHAT", "text": "All AI models failed to respond."}

        # Pick the best response based on 'score'
        valid_responses.sort(key=lambda x: x.get("score", 0), reverse=True)
        return valid_responses[0]

    @classmethod
    async def _call_cerebras(cls, query, system) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.cerebras.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "llama3.1-8b",
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": query}],
                        "response_format": { "type": "json_object" }
                    },
                    timeout=10.0
                )
                return json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception: return {}

    @classmethod
    async def _call_groq(cls, query, system) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": query}],
                        "response_format": { "type": "json_object" }
                    },
                    timeout=10.0
                )
                return json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception: return {}

    @classmethod
    async def _call_gemini(cls, query, system) -> Dict[str, Any]:
        try:
            if not GEMINI_API_KEY:
                return {}

            full_prompt = f"{system}\n\nUser Query: {query}\nResponse must be JSON."
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                    params={"key": GEMINI_API_KEY},
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": full_prompt}
                                ]
                            }
                        ],
                        "generationConfig": {
                            "response_mime_type": "application/json"
                        }
                    },
                    timeout=15.0,
                )
                payload = response.json()

            text = (
                payload.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
            return {}
        except Exception: return {}

    @classmethod
    async def _call_openai(cls, query, system) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": query}],
                        "response_format": { "type": "json_object" }
                    },
                    timeout=15.0
                )
                return json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception: return {}

    @staticmethod
    def _clean_data(data: Any) -> Dict[str, Any]:
        if not data or not isinstance(data, dict): return {}
        cleaned = {}
        for k, v in data.items():
            if v == "None" or v == "null" or v == "" or v == "ID_HERE": 
                cleaned[k] = None
            elif v in ["True", "true", True]: 
                cleaned[k] = True
            elif v in ["False", "false", False]: 
                cleaned[k] = False
            elif isinstance(v, str):
                if v.isdigit():
                    cleaned[k] = int(v)
                else:
                    num_clean = re.sub(r'[^\d.]', '', v)
                    if num_clean and v.startswith(('₩', '$')):
                        try: cleaned[k] = int(float(num_clean))
                        except: cleaned[k] = v
                    else:
                        cleaned[k] = v
            else:
                cleaned[k] = v
        return cleaned

    @classmethod
    @handle_agent_errors
    async def _execute_intent(
        cls,
        db: Session,
        agent_output: Dict[str, Any],
        user_query: str,
        conversation_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        intent = str(agent_output.get("intent") or "CHAT").upper()
        obj = str(agent_output.get("object_type") or "").lower()
        record_id = agent_output.get("record_id")
        data = agent_output.get("data") or {}
        sql = agent_output.get("sql")

        if record_id == "ID_HERE": record_id = None

        if intent == "CHAT":
            ConversationContextStore.remember_object(conversation_id, obj, intent)
            return agent_output

        if intent == "SEND_MESSAGE":
            selection_payload = agent_output.get("selection") or ConversationContextStore.get_selection(conversation_id)
            if selection_payload:
                agent_output["selection"] = selection_payload
            return agent_output

        if intent == "USAGE":
            agent_output["text"] = (
                "Currently, I use four different AI providers to ensure the best response. "
                "You can check your remaining tokens/quota at their respective dashboards:\n\n"
                "1. **Cerebras**: [Cerebras Cloud](https://cloud.cerebras.ai/)\n"
                "2. **Groq**: [Groq Console](https://console.groq.com/settings/limits)\n"
                "3. **Gemini**: [Google AI Studio](https://aistudio.google.com/app/plan)\n"
                "4. **OpenAI**: [OpenAI Usage](https://platform.openai.com/usage)\n\n"
                "Is there anything else I can help you with?"
            )
            return agent_output

        if intent == "MODIFY_UI":
            q_low = user_query.lower()
            
            # 1. Handle Home Screen Recommendation Logic Changes
            if "ai recommend" in q_low or "추천" in q_low:
                if "hot" in q_low or "따끈" in q_low:
                    AIRecommendationService.set_recommendation_mode("Hot Deals")
                    agent_output["text"] = "I've set the AI Recommendation logic to **Hot Deals** (Recent Test Drives). Please refresh the dashboard or click [AI Recommend] to see the results!"
                elif "high" in q_low or "금액" in q_low or "비싼" in q_low:
                    AIRecommendationService.set_recommendation_mode("High Value")
                    agent_output["text"] = "I've set the AI Recommendation logic to **High Value** (Deals over 50M). Please refresh the dashboard or click [AI Recommend] to see the results!"
                elif "closing" in q_low or "마감" in q_low or "급한" in q_low:
                    AIRecommendationService.set_recommendation_mode("Closing Soon")
                    agent_output["text"] = "I've set the AI Recommendation logic to **Closing Soon** (Final Negotiation stage). Please refresh the dashboard or click [AI Recommend] to see the results!"
                elif "default" in q_low or "기본" in q_low:
                    AIRecommendationService.set_recommendation_mode("Default")
                    agent_output["text"] = "I've restored the AI Recommendation logic to **Default** (Most recent). Please refresh the dashboard or click [AI Recommend] to see the results!"
                else:
                    # Ask for logic preference
                    agent_output["intent"] = "CHAT"
                    current_mode = AIRecommendationService.get_recommendation_mode()
                    agent_output["text"] = f"The current **AI Recommend** logic is **{current_mode}**. How would you like to change it? \n\nOptions: [Hot Deals], [High Value], [Closing Soon], or [Default]."
                
                return agent_output

            # 2. Handle Chat Table CSS Style Changes
            if any(word in q_low for word in ["compact", "축소", "작게"]):
                agent_output["text"] = "I've updated the table to the **Compact** style for you."
            elif any(word in q_low for word in ["modern", "모던", "깔끔"]):
                agent_output["text"] = "I've applied the **Modern** grid style to the table."
            elif any(word in q_low for word in ["default", "기본", "원래"]):
                agent_output["text"] = "I've restored the table to the **Default** Salesforce style."
            elif any(mode in q_low for mode in ["hot deals", "high value", "closing soon"]):
                # This should have been caught in section 1 above, but if we're here, 
                # something was missed. Let's re-run the mode check.
                if "high value" in q_low:
                    AIRecommendationService.set_recommendation_mode("High Value")
                    agent_output["text"] = "I've set the AI Recommendation logic to **High Value** (Deals over 50M). Please refresh the dashboard or click [AI Recommend] to see the results!"
                elif "hot deals" in q_low:
                    AIRecommendationService.set_recommendation_mode("Hot Deals")
                    agent_output["text"] = "I've set the AI Recommendation logic to **Hot Deals** (Recent Test Drives). Please refresh the dashboard or click [AI Recommend] to see the results!"
                elif "closing soon" in q_low:
                    AIRecommendationService.set_recommendation_mode("Closing Soon")
                    agent_output["text"] = "I've set the AI Recommendation logic to **Closing Soon** (Final Negotiation stage). Please refresh the dashboard or click [AI Recommend] to see the results!"
            else:
                agent_output["intent"] = "CHAT"
                current_mode = AIRecommendationService.get_recommendation_mode()
                agent_output["text"] = f"The current **AI Recommend** logic is **{current_mode}**. How would you like to change it? You can choose [Hot Deals], [High Value], [Closing Soon], or [Default]."
            
            return agent_output

        if intent == "RECOMMEND":
            safe_page, safe_per_page, offset = cls._sanitize_pagination(page, per_page)
            fetch_limit = max(safe_page * safe_per_page, 50)
            recommends = AIRecommendationService.get_ai_recommendations(db, limit=fetch_limit)
            paged_recommends = recommends[offset:offset + safe_per_page]
            current_mode = AIRecommendationService.get_recommendation_mode()
            agent_output["results"] = []
            for r in paged_recommends:
                agent_output["results"].append({
                    "id": r.id,
                    "name": r.name,
                    "amount": f"₩{r.amount:,}" if r.amount else "₩0",
                    "stage": r.stage,
                    "temperature": getattr(r, 'temp_display', 'Hot')
                })
            agent_output["object_type"] = "opportunity"
            total = len(recommends)
            total_pages = max(1, (total + safe_per_page - 1) // safe_per_page)
            agent_output["pagination"] = {
                "page": safe_page,
                "per_page": safe_per_page,
                "total": total,
                "total_pages": total_pages,
                "object_type": "opportunity",
            }
            agent_output["original_query"] = user_query
            agent_output["text"] = f"Here are {len(paged_recommends)} AI-recommended deals for you. Current logic: **{current_mode}**."
            return agent_output
        
        if intent == "MANAGE":
            if not record_id:
                if "just created" in user_query.lower() or "방금" in user_query:
                    mapping_table = {"lead": "leads", "contact": "contacts", "opportunity": "opportunities"}
                    table = mapping_table.get(obj)
                    if table:
                        last_res = db.execute(text(f"SELECT id FROM {table} WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 1")).fetchone()
                        if last_res: record_id = last_res[0]

            if not record_id:
                return {"intent": "CHAT", "text": "I need a record ID to manage it. Please select a record from the list."}
            
            record_details = ""
            template_image_url = None
            if obj in ["lead", "leads"]:
                lead = LeadService.get_lead(db, record_id)
                if lead: record_details = f"Lead: {lead.first_name} {lead.last_name} ({lead.status})"
            elif obj in ["contact", "contacts"]:
                contact = ContactService.get_contact(db, record_id)
                if contact: record_details = f"Contact: {contact.first_name} {contact.last_name} ({contact.email})"
            elif obj in ["opportunity", "opportunities", "opps"]:
                opp = OpportunityService.get_opportunity(db, record_id)
                if opp: record_details = f"Opportunity: {opp.name} ({opp.stage} - ₩{opp.amount})"
            elif obj in ["message_template", "template"]:
                template = MessageTemplateService.get_template(db, record_id)
                if template:
                    template_image_url = getattr(template, "image_url", None)
                    image_note = " with image" if template_image_url else ""
                    record_details = f"Template: {template.name} ({template.subject}){image_note}"
            
            if record_details:
                fields_list = []
                if obj in ["lead", "leads"]: fields_list = ["First Name", "Last Name", "Email", "Phone", "Status"]
                elif obj in ["contact", "contacts"]: fields_list = ["First Name", "Last Name", "Email", "Phone", "Status"]
                elif obj in ["opportunity", "opportunities", "opps"]: fields_list = ["Name", "Amount", "Stage", "Probability"]
                elif obj in ["message_template", "template"]: fields_list = ["Name", "Subject", "Content", "Record Type", "Image URL"]
                
                button_html = " ".join([f"[{f}]" for f in fields_list])
                template_image_html = ""
                if obj in ["message_template", "template"] and template_image_url:
                    template_image_html = f"<br><br><img src=\"{template_image_url}\" alt=\"Template image\" style=\"max-width:180px;border-radius:10px;border:1px solid #d7deeb;\"><br><a href=\"{template_image_url}\" target=\"_blank\" style=\"font-size:0.8rem;color:#0176d3;\">Open template image</a>"
                agent_output["text"] = f"I've selected **{record_details}** (ID: {record_id}). \n\nFields you can update:\n{button_html}\n\nWhat would you like to do?{template_image_html}"
                agent_output["record_id"] = record_id
                ConversationContextStore.remember_object(conversation_id, obj, intent, record_id=record_id)
            else:
                agent_output["text"] = f"I couldn't find the {obj} record with ID {record_id}."
            
            return agent_output

        mapping = {
            "leads": "lead", "contacts": "contact", "opportunities": "opportunity", "opps": "opportunity",
            "brands": "brand", "models": "model", "products": "product", "assets": "asset",
            "templates": "message_template", "message_templates": "message_template",
            "messages": "message_send", "message_sends": "message_send"
        }
        obj = mapping.get(obj, obj)

        if intent == "QUERY":
            if not sql:
                config = cls._default_query_parts(obj)
                if config:
                    sql = (
                        f"SELECT {config['select']} FROM {config['from']} "
                        f"WHERE {config['where']} ORDER BY {config['order_by']}"
                    )
            
            if sql:
                try:
                    sql = sql.replace("FROM messages", "FROM message_sends").replace("from messages", "from message_sends")
                    paged = cls._execute_paginated_query(db, sql, obj, page, per_page)
                    agent_output["results"] = paged["results"]
                    agent_output["sql"] = paged["sql"]
                    agent_output["pagination"] = paged["pagination"]
                    agent_output["original_query"] = user_query
                    ConversationContextStore.remember_object(conversation_id, obj, intent)
                    return agent_output
                except Exception as e:
                    logger.error(f"SQL Error: {str(e)}")
                    return {"intent": "CHAT", "text": f"Database query failed: {str(e)}"}

        data = cls._clean_data(data)
        
        if intent == "CREATE":
            if obj == "lead":
                res = LeadService.create_lead(db, **data)
                agent_output["text"] = f"Success! Created Lead {res.first_name} {res.last_name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, res.id)
                return agent_output
            elif obj == "contact":
                res = ContactService.create_contact(db, **data)
                name = getattr(res, "name", None) or f"{res.first_name} {res.last_name}"
                agent_output["text"] = f"Success! Created Contact {name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, res.id)
                return agent_output
            elif obj == "opportunity":
                res = OpportunityService.create_opportunity(db, **data)
                agent_output["text"] = f"Success! Created Opportunity {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, res.id)
                return agent_output
            elif obj == "brand":
                data["record_type"] = "Brand"
                res = VehicleSpecService.create_spec(db, **data)
                agent_output["text"] = f"Success! Created Brand {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, res.id)
                return agent_output
            elif obj == "model":
                res = ModelService.create_model(db, **data)
                agent_output["text"] = f"Success! Created Model {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, res.id)
                return agent_output
            elif obj == "product":
                from backend.app.services.product_service import ProductService
                res = ProductService.create_product(db, **data)
                agent_output["text"] = f"Success! Created Product {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, res.id)
                return agent_output
            elif obj == "asset":
                from backend.app.services.asset_service import AssetService
                res = AssetService.create_asset(db, **data)
                agent_output["text"] = f"Success! Registered Asset with VIN {res.vin} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, res.id)
                return agent_output
            elif obj in ["message_template", "template"]:
                name = data.pop("name", "New Template")
                res = MessageTemplateService.create_template(db, name=name, **data)
                agent_output["text"] = f"Success! Created Template: {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, "message_template", res.id)
                return agent_output

        if intent == "UPDATE" and record_id:
            if obj == "lead":
                res = LeadService.update_lead(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Lead {record_id}." if res else f"Lead {record_id} not found."
                return agent_output
            elif obj == "contact":
                res = ContactService.update_contact(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Contact {record_id}." if res else f"Contact {record_id} not found."
                return agent_output
            elif obj == "opportunity":
                res = OpportunityService.update_opportunity(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Opportunity {record_id}." if res else f"Opportunity {record_id} not found."
                return agent_output
            elif obj == "brand":
                res = VehicleSpecService.update_vehicle_spec(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Brand {record_id}." if res else f"Brand {record_id} not found."
                return agent_output
            elif obj == "model":
                res = ModelService.update_model(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Model {record_id}." if res else f"Model {record_id} not found."
                return agent_output
            elif obj == "product":
                from backend.app.services.product_service import ProductService
                res = ProductService.update_product(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Product {record_id}." if res else f"Product {record_id} not found."
                return agent_output
            elif obj == "asset":
                from backend.app.services.asset_service import AssetService
                res = AssetService.update_asset(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Asset {record_id}." if res else f"Asset {record_id} not found."
                return agent_output
            elif obj in ["message_template", "template"]:
                res = MessageTemplateService.update_template(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Template {record_id}." if res else f"Template {record_id} not found."
                return agent_output

        if intent == "DELETE" and record_id:
            if obj == "lead":
                success = LeadService.delete_lead(db, record_id)
                agent_output["text"] = f"Success! Deleted Lead {record_id}." if success else f"Lead {record_id} not found."
                return agent_output
            elif obj == "contact":
                success = ContactService.delete_contact(db, record_id)
                agent_output["text"] = f"Success! Deleted Contact {record_id}." if success else f"Contact {record_id} not found."
                return agent_output
            elif obj == "opportunity":
                success = OpportunityService.delete_opportunity(db, record_id)
                agent_output["text"] = f"Success! Deleted Opportunity {record_id}." if success else f"Opportunity {record_id} not found."
                return agent_output
            elif obj == "brand":
                success = VehicleSpecService.delete_vehicle_spec(db, record_id)
                agent_output["text"] = f"Success! Deleted Brand {record_id}." if success else f"Brand {record_id} not found."
                return agent_output
            elif obj == "model":
                success = ModelService.delete_model(db, record_id)
                agent_output["text"] = f"Success! Deleted Model {record_id}." if success else f"Model {record_id} not found."
                return agent_output
            elif obj == "product":
                from backend.app.services.product_service import ProductService
                success = ProductService.delete_product(db, record_id)
                agent_output["text"] = f"Success! Deleted Product {record_id}." if success else f"Product {record_id} not found."
                return agent_output
            elif obj == "asset":
                from backend.app.services.asset_service import AssetService
                success = AssetService.delete_asset(db, record_id)
                agent_output["text"] = f"Success! Deleted Asset {record_id}." if success else f"Asset {record_id} not found."
                return agent_output
            elif obj in ["message_template", "template"]:
                success = MessageTemplateService.delete_template(db, record_id)
                agent_output["text"] = f"Success! Deleted Template {record_id}." if success else f"Template {record_id} not found."
                return agent_output

        return agent_output
