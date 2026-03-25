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
from web.backend.app.services.lead_service import LeadService
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.opportunity_service import OpportunityService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService
from web.backend.app.services.model_service import ModelService
from web.message.backend.services.message_template_service import MessageTemplateService
from web.message.backend.services.message_service import MessageService
from web.backend.app.utils.error_handler import handle_agent_errors
from ai_agent.llm.backend.recommendations import AIRecommendationService
from ai_agent.llm.backend.intent_preclassifier import IntentPreClassifier
from ai_agent.llm.backend.conversation_context import ConversationContextStore
from ai_agent.llm.backend.intent_reasoner import IntentReasoner

load_dotenv()

logger = logging.getLogger(__name__)

# API Keys from .env
CEREBRAS_API_KEY = os.getenv("CELEBRACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Skills directory is 3 levels up from this file
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_PATH = os.path.join(SKILLS_DIR, "llm", "backend", "metadata.json")

class AiAgentService:
    LEAD_STATUS_ALIASES = {
        "new": "New",
        "follow up": "Follow Up",
        "follow-up": "Follow Up",
        "qualified": "Qualified",
        "lost": "Lost",
        "신규": "New",
        "팔로우업": "Follow Up",
        "후속": "Follow Up",
        "자격": "Qualified",
        "실패": "Lost",
        "유실": "Lost",
    }

    LEAD_UPDATE_FIELD_ALIASES = {
        "first_name": ["first name", "firstname", "이름"],
        "last_name": ["last name", "lastname", "surname"],
        "status": ["status", "상태"],
        "email": ["email", "이메일", "메일"],
        "phone": ["phone", "mobile", "휴대폰", "전화"],
        "gender": ["gender", "성별"],
        "description": ["description", "desc", "note", "메모", "설명"],
    }

    LEAD_EDIT_CONTEXT_INTENTS = {"CREATE", "MANAGE", "UPDATE"}

    @classmethod
    def _extract_lead_fields_from_text(cls, user_query: str, allow_loose_last_name: bool = True) -> Dict[str, Any]:
        text = user_query.strip()
        lower = text.lower()
        data: Dict[str, Any] = {}

        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if email_match:
            data["email"] = email_match.group(0)

        phone_match = re.search(r"(?:\+?\d[\d\-\s]{7,}\d)", text)
        if phone_match:
            data["phone"] = re.sub(r"\D", "", phone_match.group(0))

        for key, value in cls.LEAD_STATUS_ALIASES.items():
            if key in lower:
                data["status"] = value
                break

        last_name_match = re.search(r"last name\s+([A-Za-z가-힣-]+)", text, re.IGNORECASE)
        if last_name_match:
            data["last_name"] = last_name_match.group(1)

        if allow_loose_last_name and "last_name" not in data:
            cleaned = re.sub(r"[,:]", " ", text)
            tokens = [tok for tok in cleaned.split() if tok and "@" not in tok and not re.fullmatch(r"\d+", tok)]
            stop_words = {"create", "lead", "for", "status", "email", "phone", "new", "qualified", "lost", "show", "recent", "follow", "up"}
            candidate_tokens = [tok for tok in tokens if tok.lower() not in stop_words]
            if candidate_tokens:
                data["last_name"] = candidate_tokens[-1]

        return data

    @classmethod
    def _extract_lead_update_fields_from_text(cls, user_query: str) -> Dict[str, Any]:
        text = user_query.strip()
        lower = text.lower()
        data = cls._extract_lead_fields_from_text(text, allow_loose_last_name=False)
        clear_words = ["clear", "remove", "blank", "empty", "none", "delete", "지워", "삭제", "비워"]
        clear_pattern = "|".join(re.escape(word) for word in clear_words)

        for field, aliases in cls.LEAD_UPDATE_FIELD_ALIASES.items():
            alias_pattern = "|".join(re.escape(alias) for alias in aliases)
            if re.search(rf"(?:{clear_pattern})\s+(?:the\s+)?(?:{alias_pattern})(?:\b|$)", lower):
                data[field] = None
                continue
            if re.search(rf"(?:{alias_pattern})\s*(?:is|to|=|:)?\s*(?:blank|empty|none|clear)\b", lower):
                data[field] = None

        extra_patterns = {
            "first_name": [r"first name\s*(?:is|to|=|:)?\s*([A-Za-z가-힣-]+)", r"(?:^|\s)이름(?:은|는|을|를)?\s+([A-Za-z가-힣-]+)"],
            "last_name": [r"last name\s*(?:is|to|=|:)?\s*([A-Za-z가-힣-]+)", r"(?:^|\s)성(?:은|는|을|를)?\s+([A-Za-z가-힣-]+)"],
            "gender": [r"gender\s*(?:is|to|=|:)?\s*([A-Za-z가-힣-]+)", r"(?:^|\s)성별(?:은|는|을|를)?\s+([A-Za-z가-힣-]+)"],
            "description": [r"description\s*(?:is|to|=|:)?\s*(.+)", r"(?:^|\s)(?:note|메모|설명)(?:는|은|을|를)?\s+(.+)"],
        }
        for field, patterns in extra_patterns.items():
            if field in data:
                continue
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1).strip().strip(".,")
                    if value:
                        data[field] = value
                        break

        return data

    @classmethod
    def _guide_pending_lead_create(cls, collected: Dict[str, Any], language_preference: Optional[str]) -> Dict[str, Any]:
        missing = []
        if not collected.get("last_name"):
            missing.append("last name")
        if not collected.get("status"):
            missing.append("status")

        is_korean = (language_preference or "").lower() == "kor"
        if is_korean:
            prompt = "리드 생성을 이어가볼게요. "
            if missing:
                prompt += f"아직 {', '.join(missing)} 정보가 필요해요. "
            prompt += "예: `last name Kim, status New`, `성이 김이고 상태는 Follow Up`, `이메일 kim@test.com, status Qualified`"
        else:
            prompt = "Let's keep creating the lead. "
            if missing:
                prompt += f"I still need {', '.join(missing)}. "
            prompt += "For example: `last name Kim, status New`, `status Follow Up`, or `email kim@test.com, status Qualified`."
        return {"intent": "CHAT", "object_type": "lead", "text": prompt, "score": 1.0}

    @classmethod
    def _resolve_pending_create(cls, user_query: str, conversation_id: Optional[str], language_preference: Optional[str]) -> Optional[Dict[str, Any]]:
        pending = ConversationContextStore.get_pending_create(conversation_id)
        if not pending:
            return None

        object_type = pending.get("object_type")
        if object_type != "lead":
            return None

        collected = dict(pending.get("data") or {})
        collected.update({k: v for k, v in cls._extract_lead_fields_from_text(user_query).items() if v})

        if not collected.get("last_name") or not collected.get("status"):
            ConversationContextStore.remember_pending_create(conversation_id, object_type, collected)
            return cls._guide_pending_lead_create(collected, language_preference)

        ConversationContextStore.clear_pending_create(conversation_id)
        return {
            "intent": "CREATE",
            "object_type": "lead",
            "data": collected,
            "score": 1.0,
        }

    @classmethod
    def _resolve_pending_lead_edit(cls, user_query: str, conversation_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not conversation_id:
            return None

        context = ConversationContextStore.get_context(conversation_id)
        if context.get("last_object") != "lead" or not context.get("last_record_id"):
            return None
        if context.get("last_intent") not in cls.LEAD_EDIT_CONTEXT_INTENTS:
            return None

        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        if explicit_objects and "lead" not in explicit_objects:
            return None

        data = cls._extract_lead_update_fields_from_text(user_query)
        if not data:
            return None

        return {
            "intent": "UPDATE",
            "object_type": "lead",
            "record_id": context.get("last_record_id"),
            "data": data,
            "score": 1.0,
        }

    @classmethod
    def _apply_contextual_record_id(cls, agent_output: Dict[str, Any], conversation_id: Optional[str]) -> Dict[str, Any]:
        if not conversation_id:
            return agent_output

        intent = str(agent_output.get("intent") or "").upper()
        if intent != "UPDATE" or agent_output.get("record_id"):
            return agent_output

        context = ConversationContextStore.get_context(conversation_id)
        last_object = context.get("last_object")
        last_record_id = context.get("last_record_id")
        object_type = str(agent_output.get("object_type") or "").lower()
        object_type = {"leads": "lead", "contacts": "contact", "opportunities": "opportunity"}.get(object_type, object_type)

        if last_object and last_record_id and (not object_type or object_type == last_object):
            agent_output["object_type"] = last_object
            agent_output["record_id"] = last_record_id

        return agent_output

    @classmethod
    def _resolve_explicit_manage_request(cls, user_query: str) -> Optional[Dict[str, Any]]:
        match = re.search(r"manage\s+(\w+)\s+([\w-]+)", user_query, re.IGNORECASE)
        if not match:
            return None
        return {
            "intent": "MANAGE",
            "object_type": match.group(1).lower(),
            "record_id": match.group(2),
            "score": 1.0,
        }

    @staticmethod
    def _delete_record(db: Session, obj: str, record_id: str) -> bool:
        if obj == "lead":
            return LeadService.delete_lead(db, record_id)
        if obj == "contact":
            return ContactService.delete_contact(db, record_id)
        if obj == "opportunity":
            return OpportunityService.delete_opportunity(db, record_id)
        if obj == "brand":
            return VehicleSpecService.delete_vehicle_spec(db, record_id)
        if obj == "model":
            return ModelService.delete_model(db, record_id)
        if obj == "product":
            from web.backend.app.services.product_service import ProductService
            return ProductService.delete_product(db, record_id)
        if obj == "asset":
            from web.backend.app.services.asset_service import AssetService
            return AssetService.delete_asset(db, record_id)
        if obj in ["message_template", "template"]:
            return MessageTemplateService.delete_template(db, record_id)
        return False

    @staticmethod
    def _object_display_label(obj: str, total: int) -> str:
        labels = {
            "lead": ("lead", "leads"),
            "contact": ("contact", "contacts"),
            "opportunity": ("opportunity", "opportunities"),
            "brand": ("brand", "brands"),
            "model": ("model", "models"),
            "product": ("product", "products"),
            "asset": ("asset", "assets"),
            "message_template": ("message template", "message templates"),
            "message_send": ("message", "messages"),
        }
        singular, plural = labels.get(obj, (obj.replace("_", " "), f"{obj.replace('_', ' ')}s"))
        return singular if total == 1 else plural

    @classmethod
    def _default_query_text(cls, obj: str, pagination: Dict[str, Any]) -> str:
        total = int((pagination or {}).get("total") or 0)
        label = cls._object_display_label(obj, total)
        if total == 0:
            return f"I couldn't find any {label}."

        page = int((pagination or {}).get("page") or 1)
        total_pages = int((pagination or {}).get("total_pages") or 1)
        if total_pages > 1:
            return f"I found {total} {label}. You're viewing page {page} of {total_pages}."
        return f"I found {total} {label} for you."

    @staticmethod
    def _display_value(value: Any) -> str:
        if value in (None, "", "None", "null"):
            return "Blank"
        if hasattr(value, "value"):
            return str(value.value)
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value)

    @staticmethod
    def _lead_name(lead: Any) -> str:
        return " ".join(
            part for part in [getattr(lead, "first_name", None), getattr(lead, "last_name", None)] if part
        ).strip() or "Unnamed Lead"

    @classmethod
    def _lead_delete_summary(cls, lead: Any) -> str:
        name = cls._lead_name(lead)
        phone = cls._display_value(getattr(lead, "phone", None))
        if phone != "Blank":
            return f"{name} ({phone})"
        return name

    @classmethod
    def _detect_manage_mode(cls, user_query: str) -> str:
        normalized = IntentPreClassifier.normalize(user_query)
        if any(token in normalized for token in ["edit", "update", "change", "modify", "수정", "변경", "바꿔"]):
            return "edit"
        return "view"

    @classmethod
    def _build_lead_create_form_response(cls, language_preference: Optional[str]) -> Dict[str, Any]:
        is_korean = (language_preference or "").lower() == "kor"
        return {
            "intent": "OPEN_FORM",
            "object_type": "lead",
            "form_url": "/leads/new-modal",
            "form_title": "New Lead",
            "form_kind": "lead_create",
            "text": (
                "리드 생성 폼을 여기 대화창에 띄웠어요. 필요한 값을 입력하고 저장해 주세요."
                if is_korean else
                "I opened the lead create form here in chat. Fill in the fields you want, then save it."
            ),
            "score": 1.0,
        }

    @classmethod
    def _build_lead_edit_form_response(
        cls,
        record_id: str,
        lead_name: str,
        language_preference: Optional[str],
    ) -> Dict[str, Any]:
        is_korean = (language_preference or "").lower() == "kor"
        return {
            "intent": "OPEN_FORM",
            "object_type": "lead",
            "record_id": record_id,
            "form_url": f"/leads/new-modal?id={record_id}",
            "form_title": f"Edit {lead_name}",
            "form_kind": "lead_edit",
            "text": (
                f"리드 **{lead_name}** 수정 폼을 여기 대화창에 띄웠어요. 바로 수정하고 저장해 주세요."
                if is_korean else
                f"I opened the edit form for **{lead_name}** here in chat. Update the fields you want, then save it."
            ),
            "score": 1.0,
        }

    @classmethod
    def _build_lead_chat_card(cls, db: Session, lead: Any, mode: str = "view") -> Dict[str, Any]:
        from web.backend.app.services.product_service import ProductService

        brand = VehicleSpecService.get_vehicle_spec(db, lead.brand) if getattr(lead, "brand", None) else None
        model = ModelService.get_model(db, lead.model) if getattr(lead, "model", None) else None
        product = ProductService.get_product(db, lead.product) if getattr(lead, "product", None) else None

        name = cls._lead_name(lead)
        status = cls._display_value(getattr(lead, "status", None))
        fields = [
            {"label": "First name", "value": cls._display_value(getattr(lead, "first_name", None))},
            {"label": "Last name", "value": cls._display_value(getattr(lead, "last_name", None))},
            {"label": "Status", "value": status},
            {"label": "Email", "value": cls._display_value(getattr(lead, "email", None))},
            {"label": "Phone", "value": cls._display_value(getattr(lead, "phone", None))},
            {"label": "Gender", "value": cls._display_value(getattr(lead, "gender", None))},
            {"label": "Brand", "value": cls._display_value(getattr(brand, "name", None))},
            {"label": "Model", "value": cls._display_value(getattr(model, "name", None))},
            {"label": "Product", "value": cls._display_value(getattr(product, "name", None))},
            {"label": "Description", "value": cls._display_value(getattr(lead, "description", None))},
        ]
        line_count = 2 + len(fields)
        hint = (
            "Reply with the fields to change, like `status Qualified`, `phone 01012345678`, or `email kim@test.com`."
            if mode == "edit" else
            "Reply with `edit this lead` to keep updating in chat, or ask to send a message."
        )
        actions = []
        if mode == "view":
            actions = [
                {"label": "Edit", "action": "edit", "tone": "primary"},
                {"label": "Send Message", "action": "send_message", "tone": "secondary"},
                {"label": "Delete", "action": "delete", "tone": "danger"},
            ]

        return {
            "type": "lead_paste",
            "object_type": "lead",
            "mode": mode,
            "paste_label": f"Pasted ~{line_count} lines",
            "title": name,
            "subtitle": f"Lead · {status}",
            "record_id": str(getattr(lead, "id", "")),
            "fields": fields,
            "actions": actions,
            "hint": hint,
        }

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
        safe_per_page = max(1, min(int(per_page or 30), 30))
        offset = (safe_page - 1) * safe_per_page
        return safe_page, safe_per_page, offset

    @staticmethod
    def _default_query_parts(obj: str) -> Optional[Dict[str, str]]:
        mapping = {
            "lead": {
                "select": "id, first_name, last_name, email, phone, status, created_at",
                "from": "leads",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "contact": {
                "select": "id, first_name, last_name, email, phone, tier, last_interaction_at, created_at",
                "from": "contacts",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "opportunity": {
                "select": "o.id, o.name, o.stage, o.temperature, o.amount, o.status, o.is_followed, o.close_date, o.updated_at, c.first_name || ' ' || c.last_name AS contact_display_name, c.phone AS contact_phone, m.name AS model_name",
                "from": "opportunities o LEFT JOIN contacts c ON o.contact = c.id LEFT JOIN models m ON o.model = m.id",
                "where": "o.deleted_at IS NULL",
                "order_by": "o.created_at DESC",
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

    @staticmethod
    def _apply_search_to_sql(obj: str, config: Dict[str, str], term: str) -> Dict[str, str]:
        if not term:
            return config
        
        search_fields = {
            "lead": ["first_name", "last_name", "email", "phone", "status"],
            "contact": ["first_name", "last_name", "email", "phone"],
            "opportunity": ["o.name", "o.stage", "o.temperature"],
            "product": ["name", "category"],
            "asset": ["vin", "plate_number"],
            "message_template": ["name", "subject", "content"],
        }
        
        fields = search_fields.get(obj, ["id"])
        term_clean = term.replace("'", "''")
        conditions = [f"{f} ILIKE '%{term_clean}%'" for f in fields]
        search_where = f"({ ' OR '.join(conditions) })"
        
        config_copy = config.copy()
        if config_copy.get("where"):
            config_copy["where"] = f"{config_copy['where']} AND {search_where}"
        else:
            config_copy["where"] = search_where
        return config_copy

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
        recent_markers = ["just created", "recently created", "방금 생성", "방금 생성한", "방금 만든", "최근 만든", "최근 생성"]
        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        if explicit_objects and object_type not in explicit_objects:
            return None

        if any(marker in q_low or marker in user_query for marker in recent_markers):
            recent_object_type = last_created.get("object_type") or object_type
            recent_record_id = last_created.get("record_id") or record_id
            if not recent_object_type or not recent_record_id:
                return None
            return {
                "intent": "MANAGE",
                "object_type": recent_object_type,
                "record_id": recent_record_id,
                "score": 1.0,
            }

        follow_up_markers = ["that", "this", "it", "them", "those", "that one", "the one", "this one", "the record", "record", "그", "이", "해당", "방금", "최근"]
        has_follow_up_marker = any(marker in q_low or marker in user_query for marker in follow_up_markers)
        manage_markers = ["show", "open", "manage", "view", "details", "grab", "fetch", "보여", "열어", "관리", "상세"]
        update_markers = ["update", "edit", "change", "modify", "tweak", "fix", "수정", "변경", "바꿔"]

        if has_follow_up_marker and any(marker in q_low or marker in user_query for marker in manage_markers + update_markers):
            return {
                "intent": "MANAGE",
                "object_type": object_type,
                "record_id": record_id,
                "score": 1.0,
            }
        
        return None

    @classmethod
    def _resolve_delete_confirmation(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        selection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not conversation_id:
            return None

        q_low = user_query.lower()
        pending_delete = ConversationContextStore.get_pending_delete(conversation_id)
        if pending_delete:
            if any(token in q_low for token in ["yes", "confirm", "proceed", "delete it", "yes delete"]):
                ConversationContextStore.clear_pending_delete(conversation_id)
                pending_ids = pending_delete.get("ids") or []
                return {
                    "intent": "DELETE",
                    "object_type": pending_delete.get("object_type"),
                    "record_id": pending_delete.get("record_id"),
                    "selection": {"object_type": pending_delete.get("object_type"), "ids": pending_ids} if pending_ids else None,
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
        delete_markers = ["delete", "remove", "erase", "nuke", "dump", "삭제"]
        if not any(marker in q_low or marker in user_query for marker in delete_markers):
            return None

        selection_payload = selection or ConversationContextStore.get_selection(conversation_id)
        selected_ids = list((selection_payload or {}).get("ids") or [])
        selected_labels = list((selection_payload or {}).get("labels") or [])
        selected_object = (selection_payload or {}).get("object_type")
        if selected_object and selected_ids:
            ConversationContextStore.remember_pending_delete(
                conversation_id,
                selected_object,
                record_id=selected_ids[0] if len(selected_ids) == 1 else None,
                ids=selected_ids,
                labels=selected_labels,
            )
            label = selected_object.replace("_", " ")
            count = len(selected_ids)
            preview_names = ", ".join(selected_labels[:3]) if selected_labels else "selected records"
            return {
                "intent": "CHAT",
                "object_type": selected_object,
                "text": (
                    f"Delete confirmation needed: should I permanently delete these {count} {label} records ({preview_names})? "
                    "Choose [yes] to continue or [cancel] to keep them."
                    if count > 1 else
                    f"Delete confirmation needed: should I permanently delete {selected_labels[0] if selected_labels else f'this {label} record'}? Choose [yes] to continue or [cancel] to keep it."
                ),
                "score": 1.0,
            }

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
            "text": f"Delete confirmation needed: should I permanently delete this {label} record ({record_id})? Choose [yes] to continue or [cancel] to keep it.",
            "score": 1.0,
        }

    @classmethod
    def _resolve_send_message_request(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        selection: Optional[Dict[str, Any]],
        language_preference: Optional[str] = None,
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

        wants_template = "template" in q_low or "message template" in q_low

        if wants_template and not template_id:
            return {
                "intent": "CHAT",
                "text": "I can send a message with a template, but I need a current template first. Open or manage a message template, then ask me to send the message.",
                "score": 1.0,
            }

        if not object_type or not ids:
            is_korean = (language_preference or "").lower() == "kor"
            return {
                "intent": "CHAT",
                "text": (
                    "누구에게 메시지를 보낼까요? `최근 생성 된 리드를 보여줘`, `전체 연락처 보여줘`, 또는 `최근 생성 된 연락처를 보여줘`처럼 먼저 대상을 불러오고, 레코드를 선택한 뒤 메시지 전송을 요청해 주세요."
                    if is_korean else
                    "Who should I send the message to? Try `show recent leads`, `show all contacts`, or `show recently created leads`, then select one or more records and ask me to send the message."
                ),
                "score": 1.0,
            }

        return {
            "intent": "SEND_MESSAGE",
            "object_type": object_type,
            "selection": {"object_type": object_type, "ids": ids},
            "template_id": template_id,
            "redirect_url": f"/messaging/ui?sourceObject={object_type}&count={len(ids)}",
            "text": (
                f"Opening the messaging flow for {len(ids)} selected {object_type} record(s)"
                f" using your current template ({template_id})."
                if template_id else
                f"Opening the messaging flow for {len(ids)} selected {object_type} record(s)."
            ),
            "score": 1.0,
        }

    @classmethod
    async def process_query(
        cls,
        db: Session,
        user_query: str,
        conversation_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 30,
        selection: Optional[Dict[str, Any]] = None,
        language_preference: Optional[str] = None,
    ) -> Dict[str, Any]:
        ConversationContextStore.remember_selection(conversation_id, selection)

        if "attachment" in user_query.lower():
            return {
                "intent": "CHAT",
                "text": "I cannot query or manage attachments directly.",
                "score": 1.0
            }

        # ROBUST EXTRACTION: Search query (Priority before LLM)
        if "search" in user_query.lower() or "조회" in user_query or "검색" in user_query:
            match = re.search(r"search\s+(\w+).*?\s+for\s+(.+)", user_query, re.IGNORECASE)
            if match:
                obj_raw = match.group(1).lower()
                # Simple normalization
                if obj_raw.endswith('s') and obj_raw != 'assets':
                    obj_raw = obj_raw[:-1]
                
                # Verify it's a known object type before committing to this intent
                if obj_raw in ["lead", "contact", "opportunity", "product", "asset", "message_template", "message_send", "brand", "model"]:
                    agent_output = {
                        "intent": "QUERY",
                        "object_type": obj_raw,
                        "data": {"search_term": match.group(2).strip()},
                        "score": 1.0
                    }
                    return await cls._execute_intent(db, agent_output, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        pending_create_resolution = cls._resolve_pending_create(user_query, conversation_id, language_preference)
        if pending_create_resolution:
            pending_create_resolution["language_preference"] = language_preference
            return await cls._execute_intent(
                db,
                pending_create_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        pending_edit_resolution = cls._resolve_pending_lead_edit(user_query, conversation_id)
        if pending_edit_resolution:
            pending_edit_resolution["language_preference"] = language_preference
            return await cls._execute_intent(
                db,
                pending_edit_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        send_message_resolution = cls._resolve_send_message_request(
            user_query,
            conversation_id,
            selection,
            language_preference=language_preference,
        )
        if send_message_resolution:
            return await cls._execute_intent(
                db,
                send_message_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        delete_resolution = cls._resolve_delete_confirmation(user_query, conversation_id, selection)
        if delete_resolution:
            return await cls._execute_intent(db, delete_resolution, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        explicit_manage_resolution = cls._resolve_explicit_manage_request(user_query)
        if explicit_manage_resolution:
            explicit_manage_resolution["language_preference"] = language_preference
            return await cls._execute_intent(db, explicit_manage_resolution, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        contextual_response = cls._resolve_contextual_record_reference(user_query, conversation_id)
        if contextual_response:
            contextual_response["language_preference"] = language_preference
            return await cls._execute_intent(db, contextual_response, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        clarification = IntentReasoner.clarify_if_needed(user_query)
        if clarification:
            return clarification

        # ---- Phase 49: Hybrid Intent Pre-Classification ----
        rule_based = IntentPreClassifier.detect(user_query)
        if rule_based:
            normalized_query = IntentPreClassifier.normalize(user_query)
            if (
                rule_based.get("intent") == "CHAT"
                and rule_based.get("object_type") == "lead"
                and IntentPreClassifier._contains_action(normalized_query, IntentPreClassifier.ACTION_CREATE)
            ):
                return cls._build_lead_create_form_response(language_preference)
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
        UI language preference: {language_preference or 'auto'}.
        If UI language preference is `eng`, answer in English.
        If UI language preference is `kor`, answer in Korean.
        
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

        agent_output = cls._apply_contextual_record_id(agent_output, conversation_id)

        agent_output["language_preference"] = language_preference
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
                if k == "phone":
                    digits_only = re.sub(r"\D", "", v)
                    cleaned[k] = digits_only or v
                elif v.isdigit():
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
        per_page: int = 30,
    ) -> Dict[str, Any]:
        intent = str(agent_output.get("intent") or "CHAT").upper()
        obj = str(agent_output.get("object_type") or "").lower()
        record_id = agent_output.get("record_id")
        selection_payload = agent_output.get("selection") or {}
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
                "Currently, I use two different AI providers to ensure the best response. "
                "You can check your remaining tokens/quota at their respective dashboards:\n\n"
                "1. **Cerebras**: [Cerebras Cloud](https://cloud.cerebras.ai/)\n"
                "2. **Groq**: [Groq Console](https://console.groq.com/settings/limits)\n\n"
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
                elif "follow up" in q_low or "follow-up" in q_low or "followup" in q_low or "후속" in q_low or "팔로우" in q_low:
                    AIRecommendationService.set_recommendation_mode("Follow Up")
                    agent_output["text"] = "I've set the AI Recommendation logic to **Follow Up** (Recently followed-up open deals). Please refresh the dashboard or click [AI Recommend] to see the results!"
                elif "closed won" in q_low or "closing" in q_low or "마감" in q_low or "급한" in q_low or "성공" in q_low:
                    AIRecommendationService.set_recommendation_mode("Closing Soon")
                    agent_output["text"] = "I've set the AI Recommendation logic to **Closed Won** (Recently won opportunities). Please refresh the dashboard or click [AI Recommend] to see the results!"
                elif "default" in q_low or "기본" in q_low:
                    AIRecommendationService.set_recommendation_mode("Default")
                    agent_output["text"] = "I've restored the AI Recommendation logic to **New Records** (Most recently created sendable deals). Please refresh the dashboard or click [AI Recommend] to see the results!"
                else:
                    # Ask for logic preference
                    agent_output["intent"] = "CHAT"
                    current_mode = AIRecommendationService.get_recommendation_mode()
                    options = [
                        f"[Hot Deals{' (Current)' if current_mode == 'Hot Deals' else ''}]",
                        f"[Follow Up{' (Current)' if current_mode == 'Follow Up' else ''}]",
                        f"[Closed Won{' (Current)' if current_mode == 'Closing Soon' else ''}]",
                        f"[New Records{' (Current)' if current_mode == 'Default' else ''}]",
                    ]
                    agent_output["text"] = f"The current **AI Recommend** logic is **{AIRecommendationService.user_facing_mode_label(current_mode)}**. How would you like to change it? \n\nOptions: {' '.join(options)}."
                
                return agent_output

            # 2. Handle Chat Table CSS Style Changes
            if any(word in q_low for word in ["compact", "축소", "작게"]):
                agent_output["text"] = "I've updated the table to the **Compact** style for you."
            elif any(word in q_low for word in ["modern", "모던", "깔끔"]):
                agent_output["text"] = "I've applied the **Modern** grid style to the table."
            elif any(word in q_low for word in ["default", "기본", "원래"]):
                agent_output["text"] = "I've restored the table to the **Default** Salesforce style."
            elif any(mode in q_low for mode in ["hot deals", "follow up", "follow-up", "followup", "closing soon", "closed won"]):
                # This should have been caught in section 1 above, but if we're here, 
                # something was missed. Let's re-run the mode check.
                if "follow up" in q_low or "follow-up" in q_low or "followup" in q_low:
                    AIRecommendationService.set_recommendation_mode("Follow Up")
                    agent_output["text"] = "I've set the AI Recommendation logic to **Follow Up** (Recently followed-up open deals). Please refresh the dashboard or click [AI Recommend] to see the results!"
                elif "hot deals" in q_low:
                    AIRecommendationService.set_recommendation_mode("Hot Deals")
                    agent_output["text"] = "I've set the AI Recommendation logic to **Hot Deals** (Recent Test Drives). Please refresh the dashboard or click [AI Recommend] to see the results!"
                elif "closing soon" in q_low or "closed won" in q_low:
                    AIRecommendationService.set_recommendation_mode("Closing Soon")
                    agent_output["text"] = "I've set the AI Recommendation logic to **Closed Won** (Recently won opportunities). Please refresh the dashboard or click [AI Recommend] to see the results!"
            else:
                agent_output["intent"] = "CHAT"
                current_mode = AIRecommendationService.get_recommendation_mode()
                options = [
                    f"[Hot Deals{' (Current)' if current_mode == 'Hot Deals' else ''}]",
                    f"[Follow Up{' (Current)' if current_mode == 'Follow Up' else ''}]",
                    f"[Closed Won{' (Current)' if current_mode == 'Closing Soon' else ''}]",
                    f"[New Records{' (Current)' if current_mode == 'Default' else ''}]",
                ]
                agent_output["text"] = f"The current **AI Recommend** logic is **{AIRecommendationService.user_facing_mode_label(current_mode)}**. How would you like to change it? {' '.join(options)}."
            
            return agent_output

        if intent == "RECOMMEND":
            safe_page, safe_per_page, offset = cls._sanitize_pagination(page, per_page)
            fetch_limit = max(safe_page * safe_per_page, 30)
            recommends = AIRecommendationService.get_ai_recommendations(db, limit=fetch_limit)
            paged_recommends = recommends[offset:offset + safe_per_page]
            current_mode = AIRecommendationService.user_facing_mode_label(AIRecommendationService.get_recommendation_mode())
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
                if lead:
                    mode = cls._detect_manage_mode(user_query)
                    lead_name = cls._lead_name(lead) if cls._lead_name(lead) != "Unnamed Lead" else record_id
                    if mode == "edit":
                        ConversationContextStore.remember_object(conversation_id, "lead", "MANAGE", record_id=record_id)
                        return cls._build_lead_edit_form_response(record_id, lead_name, None)
                    record_details = f"Lead: {lead_name} ({lead.status})"
                    agent_output["chat_card"] = cls._build_lead_chat_card(db, lead, mode=mode)
                    if mode != "edit":
                        agent_output["text"] = (
                            f"리드 **{lead_name}** 상세 정보가 아래에 열려 있어요. 수정, 메시지 전송, 또는 다른 작업이 필요하면 바로 말씀해 주세요."
                            if agent_output.get("language_preference", "") == "kor"
                            else f"Lead **{lead_name}** is now open. You can update any field, send a message, or take any action — just tell me what you need."
                        )
                    else:
                        agent_output["text"] = (
                            f"리드 **{lead_name}** 수정 카드를 아래에 띄웠어요. 변경할 내용을 알려 주세요."
                            if agent_output.get("language_preference", "") == "kor"
                            else f"Lead **{lead_name}** edit card is open below. Tell me what to change."
                        )
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
                if obj in ["lead", "leads"] and agent_output.get("chat_card"):
                    agent_output["record_id"] = record_id
                    ConversationContextStore.remember_object(conversation_id, "lead", intent, record_id=record_id)
                    return agent_output

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
                    search_term = data.get("search_term")
                    if search_term:
                        config = cls._apply_search_to_sql(obj, config, search_term)
                    
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
                    agent_output["text"] = agent_output.get("text") or cls._default_query_text(obj, paged["pagination"])
                    ConversationContextStore.remember_object(conversation_id, obj, intent)
                    return agent_output
                except Exception as e:
                    logger.error(f"SQL Error: {str(e)}")
                    return {"intent": "CHAT", "text": f"Database query failed: {str(e)}"}

        data = cls._clean_data(data)
        
        if intent == "CREATE":
            if obj == "lead":
                res = LeadService.create_lead(db, **data)
                lead_name = cls._lead_name(res)
                is_korean = (agent_output.get("language_preference") or "").lower() == "kor"
                if is_korean:
                    agent_output["text"] = (
                        f"리드 **{lead_name}**이(가) 생성되었습니다! 🎉\n"
                        f"아래에서 상세 내용을 바로 확인하세요. 수정이나 메시지 전송이 필요하면 바로 말씀해 주세요."
                    )
                else:
                    agent_output["text"] = (
                        f"Lead **{lead_name}** has been created! 🎉\n"
                        f"The record is now open below. Tell me if you'd like to update a field, send a message, or do anything else."
                    )
                agent_output["chat_card"] = cls._build_lead_chat_card(db, res, mode="view")
                agent_output["intent"] = "OPEN_RECORD"
                agent_output["record_id"] = str(res.id)
                agent_output["redirect_url"] = f"/leads/{res.id}"
                ConversationContextStore.clear_pending_create(conversation_id)
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                ConversationContextStore.remember_object(conversation_id, "lead", "CREATE", record_id=str(res.id))
                return agent_output
            elif obj == "contact":
                res = ContactService.create_contact(db, **data)
                name = getattr(res, "name", None) or f"{res.first_name} {res.last_name}"
                agent_output["text"] = f"Success! Created Contact {name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj == "opportunity":
                res = OpportunityService.create_opportunity(db, **data)
                agent_output["text"] = f"Success! Created Opportunity {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj == "brand":
                data["record_type"] = "Brand"
                res = VehicleSpecService.create_spec(db, **data)
                agent_output["text"] = f"Success! Created Brand {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj == "model":
                res = ModelService.create_model(db, **data)
                agent_output["text"] = f"Success! Created Model {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj == "product":
                from web.backend.app.services.product_service import ProductService
                res = ProductService.create_product(db, **data)
                agent_output["text"] = f"Success! Created Product {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj == "asset":
                from web.backend.app.services.asset_service import AssetService
                res = AssetService.create_asset(db, **data)
                agent_output["text"] = f"Success! Registered Asset with VIN {res.vin} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj in ["message_template", "template"]:
                name = data.pop("name", "New Template")
                res = MessageTemplateService.create_template(db, name=name, **data)
                agent_output["text"] = f"Success! Created Template: {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, "message_template", str(res.id))
                return agent_output

        if intent == "UPDATE" and record_id:
            if obj == "lead":
                res = LeadService.update_lead(db, record_id, **data)
                if res:
                    refreshed = LeadService.get_lead(db, record_id)
                    refreshed_name = cls._lead_name(refreshed) if refreshed else record_id
                    is_korean = (agent_output.get("language_preference") or "").lower() == "kor"
                    if is_korean:
                        agent_output["text"] = (
                            f"리드 **{refreshed_name}** 정보가 업데이트되었습니다! ✅\n"
                            f"최신 상세 내용이 아래에 열려 있어요. 추가로 수정할 내용이 있으면 바로 말씀해 주세요."
                        )
                    else:
                        agent_output["text"] = (
                            f"Lead **{refreshed_name}** has been updated! ✅\n"
                            f"The refreshed record is open below. Let me know if you need any other changes."
                        )
                    if refreshed:
                        agent_output["chat_card"] = cls._build_lead_chat_card(db, refreshed, mode="view")
                    agent_output["intent"] = "OPEN_RECORD"
                    agent_output["redirect_url"] = f"/leads/{record_id}"
                    ConversationContextStore.remember_object(conversation_id, "lead", "UPDATE", record_id=record_id)
                else:
                    agent_output["text"] = f"Lead {record_id} not found."
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
                from web.backend.app.services.product_service import ProductService
                res = ProductService.update_product(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Product {record_id}." if res else f"Product {record_id} not found."
                return agent_output
            elif obj == "asset":
                from web.backend.app.services.asset_service import AssetService
                res = AssetService.update_asset(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Asset {record_id}." if res else f"Asset {record_id} not found."
                return agent_output
            elif obj in ["message_template", "template"]:
                res = MessageTemplateService.update_template(db, record_id, **data)
                agent_output["text"] = f"Success! Updated Template {record_id}." if res else f"Template {record_id} not found."
                return agent_output

        if intent == "DELETE":
            ids = list(selection_payload.get("ids") or ([] if not record_id else [record_id]))
            if ids:
                deleted = 0
                deleted_ids: List[str] = []
                deleted_summaries: List[str] = []
                for delete_id in ids:
                    lead_summary = None
                    if obj == "lead":
                        existing_lead = LeadService.get_lead(db, delete_id)
                        if existing_lead:
                            lead_summary = cls._lead_delete_summary(existing_lead)
                    if cls._delete_record(db, obj, delete_id):
                        deleted += 1
                        deleted_ids.append(delete_id)
                        if lead_summary:
                            deleted_summaries.append(lead_summary)
                label = cls._object_display_label(obj, len(ids)).title()
                if obj == "lead" and deleted_summaries:
                    if len(deleted_summaries) == 1:
                        agent_output["text"] = f"Success! Deleted lead {deleted_summaries[0]}."
                    else:
                        preview = ", ".join(deleted_summaries[:3])
                        suffix = "" if len(deleted_summaries) <= 3 else ", ..."
                        agent_output["text"] = f"Success! Deleted {deleted} leads: {preview}{suffix}."
                else:
                    agent_output["text"] = (
                        f"Success! Deleted {deleted} of {len(ids)} {label}."
                        if len(ids) > 1 else
                        (f"Success! Deleted {label} {ids[0]}." if deleted else f"{label} {ids[0]} not found.")
                    )
                # Return deleted_ids so the frontend can remove the rows from all visible tables
                agent_output["deleted_ids"] = deleted_ids
                return agent_output

        return agent_output
