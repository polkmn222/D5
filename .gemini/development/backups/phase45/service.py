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

# SDK Imports for ensemble
import openai
import google.generativeai as genai

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

load_dotenv()

logger = logging.getLogger(__name__)

# API Keys from .env
CEREBRAS_API_KEY = os.getenv("CELEBRACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_API_Key")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("ChatGPT_API_Key")

# Configure SDKs
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Skills directory is 3 levels up from this file
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_PATH = os.path.join(SKILLS_DIR, "backend", "metadata.json")

class AiAgentService:
    @classmethod
    async def _call_llm(cls, user_query: str, system_prompt: str) -> Dict[str, Any]:
        return await cls._call_multi_llm_ensemble(user_query, system_prompt)

    @staticmethod
    def _parse_agent_output(raw_output: Any) -> Dict[str, Any]:
        if isinstance(raw_output, dict):
            return raw_output

        if isinstance(raw_output, str):
            try:
                parsed = json.loads(raw_output)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return {"intent": "CHAT", "text": raw_output}

        return {}

    @staticmethod
    def _apply_local_fallbacks(agent_output: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        normalized_query = user_query.strip()
        lowered_query = normalized_query.lower()

        if lowered_query == "current created lead":
            return {"intent": "CHAT", "text": "I'm here to help with your CRM. What would you like to do?"}

        update_patterns = [
            re.compile(r"update\s+(?P<field>[\w\s]+?)\s+to\s+(?P<value>.+?)\s+for\s+(?P<object>\w+)\s+(?P<record_id>[\w-]+)$", re.IGNORECASE),
            re.compile(r"update\s+(?P<object>\w+)\s+(?P<record_id>[\w-]+)\s+(?P<field>[\w\s]+?)\s+to\s+(?P<value>.+)$", re.IGNORECASE),
        ]

        for pattern in update_patterns:
            match = pattern.fullmatch(normalized_query)
            if not match:
                continue

            current_data = agent_output.get("data")
            if current_data:
                return agent_output

            field = match.group("field").strip().lower().replace(" ", "_")
            value = match.group("value").strip().strip('"')
            return {
                **agent_output,
                "intent": "UPDATE",
                "object_type": match.group("object").lower(),
                "record_id": match.group("record_id"),
                "data": {field: value},
            }

        return agent_output

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

    @classmethod
    @handle_agent_errors
    async def process_query(cls, db: Session, user_query: str) -> Dict[str, Any]:
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
        - If a user wants to CREATE a record (lead, contact, opportunity, brand, model, product, asset, task, template) but hasn't provided mandatory info:
          1. Use intent "CHAT".
          2. Acknowledge the request.
          3. Politely ask for missing info.
             - Lead/Contact: needs at least "last_name" and "status".
             - Asset: needs "vin".
             - Task: needs "subject".
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
            "intent": "QUERY" | "CREATE" | "UPDATE" | "DELETE" | "MANAGE" | "CHAT" | "RECOMMEND",
            "text": "Helpful response here",
            "sql": "SELECT ... (if QUERY)",
            "data": {{ "field": "value" }} (if CREATE/UPDATE),
            "object_type": "lead" | "contact" | "opportunity" | "brand" | "model" | "product" | "asset" | "task" | "message_template" | "message_send",
            "record_id": "ID_HERE",
            "score": 0.0 to 1.0 (confidence in this JSON)
        }}
        """

        # Call Multi-LLM Ensemble
        agent_output = await cls._call_multi_llm_ensemble(user_query, system_prompt)
        
        # MANUAL OVERRIDE: Check for specific keyword triggers
        q_low = user_query.lower()
        if "ai recommend" in q_low or "추천" in q_low:
            agent_output["intent"] = "RECOMMEND"
        elif "send message" in q_low or "메시지 보내" in q_low:
             agent_output["intent"] = "CHAT"
             agent_output["text"] = "To send messages, please go to the [Send Messages] page. I can help you find templates or contacts to message here!"

        # ROBUST EXTRACTION: Fallback for "Manage [object] [record_id]"
        if "manage" in user_query.lower():
            match = re.search(r"manage\s+(\w+)\s+([\w-]+)", user_query, re.IGNORECASE)
            if match:
                agent_output["intent"] = "MANAGE"
                agent_output["object_type"] = match.group(1).lower()
                agent_output["record_id"] = match.group(2)

        try:
            return await cls._execute_intent(db, agent_output, user_query)
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

        # Pick the best response based on 'score' (provided by the model itself in our prompt)
        # Sort by score descending
        valid_responses.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        best = valid_responses[0]
        logger.info(f"Ensemble picked model with score {best.get('score')}. Total models: {len(valid_responses)}")
        return best

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
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Combine system and user for simple call
            full_prompt = f"{system}\n\nUser Query: {query}\nResponse must be JSON."
            response = await asyncio.to_thread(model.generate_content, full_prompt)
            # Basic JSON extraction from markdown
            text = response.text
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
            if v == "None" or v == "null" or v == "": cleaned[k] = None
            elif v in ["True", "true", True]: cleaned[k] = True
            elif v in ["False", "false", False]: cleaned[k] = False
            else: cleaned[k] = v
        return cleaned

    @classmethod
    @handle_agent_errors
    async def _execute_intent(cls, db: Session, agent_output: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        intent = str(agent_output.get("intent") or "CHAT").upper()
        obj = str(agent_output.get("object_type") or "").lower()
        record_id = agent_output.get("record_id")
        data = agent_output.get("data") or {}
        sql = agent_output.get("sql")

        if intent == "CHAT": return agent_output

        if intent == "RECOMMEND":
            recommends = AIRecommendationService.get_ai_recommendations(db, limit=5)
            agent_output["results"] = []
            for r in recommends:
                agent_output["results"].append({
                    "id": r.id,
                    "name": r.name,
                    "amount": f"₩{r.amount:,}" if r.amount else "₩0",
                    "stage": r.stage,
                    "temperature": getattr(r, 'temp_display', 'Hot')
                })
            agent_output["object_type"] = "opportunity"
            agent_output["text"] = f"Here are {len(recommends)} AI-recommended hot deals for you!"
            return agent_output
        
        if intent == "MANAGE":
            if not record_id:
                return {"intent": "CHAT", "text": "I need a record ID to manage it. Please select a record from the list."}
            
            record_details = ""
            if obj == "lead" or obj == "leads":
                lead = LeadService.get_lead(db, record_id)
                if lead: record_details = f"Lead: {lead.first_name} {lead.last_name} ({lead.status})"
            elif obj == "contact" or obj == "contacts":
                contact = ContactService.get_contact(db, record_id)
                if contact: record_details = f"Contact: {contact.first_name} {contact.last_name} ({contact.email})"
            elif obj == "opportunity" or obj == "opportunities":
                opp = OpportunityService.get_opportunity(db, record_id)
                if opp: record_details = f"Opportunity: {opp.name} ({opp.stage} - ₩{opp.amount})"
            elif obj == "message_template" or obj == "template" or obj == "message_templates":
                template = MessageTemplateService.get_template(db, record_id)
                if template: record_details = f"Template: {template.name} ({template.subject})"
            
            if record_details:
                fields_list = []
                if obj == "lead" or obj == "leads": fields_list = ["First Name", "Last Name", "Email", "Phone", "Status", "Lead Source"]
                elif obj == "contact" or obj == "contacts": fields_list = ["First Name", "Last Name", "Email", "Phone", "Status"]
                elif obj == "opportunity" or obj == "opportunities": fields_list = ["Name", "Amount", "Stage", "Probability"]
                elif obj == "message_template" or obj == "template" or obj == "message_templates": fields_list = ["Name", "Subject", "Content", "Record Type"]
                
                button_html = " ".join([f"[{f}]" for f in fields_list])
                agent_output["text"] = f"I've selected **{record_details}** (ID: {record_id}). \n\nFields you can update:\n{button_html}\n\nWhat would you like to do?"
            else:
                agent_output["text"] = f"I couldn't find the {obj} record with ID {record_id}. If this is a new record, please specify all details needed for creation."
            
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
                if obj == "lead": sql = "SELECT id, first_name, last_name, email, phone, status FROM leads WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "contact": sql = "SELECT id, first_name, last_name, email, phone, status FROM contacts WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "opportunity": sql = "SELECT id, name, stage, amount, status FROM opportunities WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "brand": sql = "SELECT id, name, record_type, description FROM vehicle_specifications WHERE record_type = 'Brand' AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "model": sql = "SELECT id, name, brand, description FROM models WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "product": sql = "SELECT id, name, brand, model, category, base_price FROM products WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "asset": sql = "SELECT id, vin, brand, model, status FROM assets WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "message_template": sql = "SELECT id, name, subject, record_type FROM message_templates WHERE deleted_at IS NULL ORDER BY created_at DESC LIMIT 10"
                elif obj == "message_send": sql = "SELECT id, contact, template, direction, status, sent_at FROM message_sends WHERE deleted_at IS NULL ORDER BY sent_at DESC LIMIT 10"
            
            if sql:
                try:
                    # Clean the object mapping for SQL queries (e.g. 'messages' -> 'message_sends')
                    sql = sql.replace("FROM messages", "FROM message_sends").replace("from messages", "from message_sends")
                    result = db.execute(text(sql))
                    agent_output["results"] = [dict(row._mapping) for row in result]
                    agent_output["sql"] = sql
                    agent_output.setdefault("text", f"I searched the database for {obj or 'records'}.")
                    return agent_output
                except Exception as e:
                    logger.error(f"SQL Error: {str(e)}")
                    return {"intent": "CHAT", "text": f"Database query failed: {str(e)}"}

        data = cls._clean_data(data)
        
        if intent == "CREATE":
            if obj == "lead":
                res = LeadService.create_lead(db, **data)
                agent_output["text"] = f"Success! Created Lead {res.first_name} {res.last_name} (ID: {res.id})."
                return agent_output
            elif obj == "contact":
                res = ContactService.create_contact(db, **data)
                name = getattr(res, "name", None) or f"{res.first_name} {res.last_name}"
                agent_output["text"] = f"Success! Created Contact {name} (ID: {res.id})."
                return agent_output
            elif obj == "opportunity":
                res = OpportunityService.create_opportunity(db, **data)
                agent_output["text"] = f"Success! Created Opportunity {res.name} (ID: {res.id})."
                return agent_output
            elif obj == "brand":
                data["record_type"] = "Brand"
                res = VehicleSpecService.create_spec(db, **data)
                agent_output["text"] = f"Success! Created Brand {res.name} (ID: {res.id})."
                return agent_output
            elif obj == "model":
                res = ModelService.create_model(db, **data)
                agent_output["text"] = f"Success! Created Model {res.name} (ID: {res.id})."
                return agent_output
            elif obj == "product":
                from backend.app.services.product_service import ProductService
                res = ProductService.create_product(db, **data)
                agent_output["text"] = f"Success! Created Product {res.name} (ID: {res.id})."
                return agent_output
            elif obj == "asset":
                from backend.app.services.asset_service import AssetService
                res = AssetService.create_asset(db, **data)
                agent_output["text"] = f"Success! Registered Asset with VIN {res.vin} (ID: {res.id})."
                return agent_output
            elif obj == "message_template" or obj == "template":
                name = data.pop("name", "New Template")
                res = MessageTemplateService.create_template(db, name=name, **data)
                agent_output["text"] = f"Success! Created Template: {res.name} (ID: {res.id})."
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
            elif obj == "message_template" or obj == "template":
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
            elif obj == "message_template" or obj == "template":
                success = MessageTemplateService.delete_template(db, record_id)
                agent_output["text"] = f"Success! Deleted Template {record_id}." if success else f"Template {record_id} not found."
                return agent_output

        return agent_output
