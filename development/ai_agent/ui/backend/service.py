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
from db.models import Model as DbModel, Product as DbProduct, VehicleSpecification
from web.backend.app.core.enums import Gender, LeadStatus, OpportunityStage, OpportunityStatus

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
from ai_agent.ui.backend.crud import (
    build_chat_native_form,
    build_lead_edit_form_response,
    build_lead_open_record_response,
    build_object_edit_form_response,
    build_object_open_record_response,
)

load_dotenv()

logger = logging.getLogger(__name__)

# API Keys from .env
CEREBRAS_API_KEY = os.getenv("CELEBRACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Skills directory is 3 levels up from this file
SKILLS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
METADATA_PATH = os.path.join(SKILLS_DIR, "backend", "metadata.json")

class AiAgentService:
    PHASE1_OBJECTS = {"lead", "contact", "opportunity"}
    CHAT_NATIVE_FORM_OBJECTS = {"lead", "contact", "opportunity"}
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
        "brand": ["brand", "브랜드"],
        "model": ["model", "모델"],
        "product": ["product", "상품"],
        "description": ["description", "desc", "note", "메모", "설명"],
    }

    LEAD_EDIT_CONTEXT_INTENTS = {"CREATE", "MANAGE", "UPDATE"}
    LEAD_READ_ACTIONS = {"show", "open", "view", "read", "details", "manage", "보여", "보여줘", "열어", "열어줘", "상세", "관리"}
    LEAD_EDIT_ACTIONS = {"edit", "수정"}
    LEAD_UPDATE_ACTIONS = {"update", "change", "modify", "변경", "바꿔"}
    LEAD_DELETE_ACTIONS = {"delete", "remove", "erase", "삭제"}
    LEAD_CREATE_ACTIONS = {"create", "add", "new", "make", "build", "생성", "만들", "등록", "추가"}
    GENERIC_CREATE_ACTIONS = LEAD_CREATE_ACTIONS
    GENERIC_UPDATE_ACTIONS = LEAD_UPDATE_ACTIONS | LEAD_EDIT_ACTIONS
    GENERIC_QUERY_ACTIONS = set(IntentPreClassifier.ACTION_QUERY) | {"recent"}
    GENERIC_READ_ACTIONS = LEAD_READ_ACTIONS
    RECENT_QUERY_MARKERS = {
        "recent",
        "latest",
        "newest",
        "most recent",
        "just created",
        "recently created",
        "방금 생성",
        "방금 생성한",
        "방금 만든",
        "최근",
        "최근 생성",
        "최근 만든",
    }
    ORDINAL_MARKERS = (
        ("first one", 0),
        ("1st one", 0),
        ("first record", 0),
        ("first", 0),
        ("latest one", 0),
        ("newest one", 0),
        ("most recent one", 0),
        ("latest", 0),
        ("newest", 0),
        ("most recent", 0),
        ("second one", 1),
        ("2nd one", 1),
        ("second", 1),
        ("third one", 2),
        ("3rd one", 2),
        ("third", 2),
        ("fourth one", 3),
        ("4th one", 3),
        ("fourth", 3),
        ("fifth one", 4),
        ("5th one", 4),
        ("fifth", 4),
    )
    CONTACT_STATUS_OPTIONS = ["New", "Contacted", "Qualified", "Junk"]
    OPPORTUNITY_STAGE_OPTIONS = [
        OpportunityStage.PROSPECTING.value,
        OpportunityStage.QUALIFICATION.value,
        OpportunityStage.TEST_DRIVE.value,
        OpportunityStage.VALUE_PROPOSITION.value,
        OpportunityStage.NEGOTIATION.value,
        OpportunityStage.PROPOSAL.value,
        OpportunityStage.CLOSED_WON.value,
        OpportunityStage.CLOSED_LOST.value,
    ]
    OPPORTUNITY_STATUS_OPTIONS = [
        OpportunityStatus.OPEN.value,
        OpportunityStatus.CLOSED_WON.value,
        OpportunityStatus.CLOSED_LOST.value,
    ]
    CHAT_NATIVE_FORM_CONFIG = {
        "lead": {
            "title_create": "Create Lead",
            "title_edit": "Edit Lead",
            "submit_create": "Create Lead",
            "submit_edit": "Save Lead",
            "fields": [
                {"name": "first_name", "label": "First Name", "control": "text", "default": ""},
                {"name": "last_name", "label": "Last Name", "control": "text", "default": "", "required": True},
                {"name": "email", "label": "Email", "control": "email", "default": ""},
                {"name": "phone", "label": "Phone", "control": "tel", "default": ""},
                {
                    "name": "status",
                    "label": "Status",
                    "control": "select",
                    "default": LeadStatus.NEW.value,
                    "required": True,
                    "options": [
                        {"value": LeadStatus.NEW.value, "label": LeadStatus.NEW.value},
                        {"value": LeadStatus.FOLLOW_UP.value, "label": LeadStatus.FOLLOW_UP.value},
                        {"value": LeadStatus.QUALIFIED.value, "label": LeadStatus.QUALIFIED.value},
                        {"value": LeadStatus.LOST.value, "label": LeadStatus.LOST.value},
                    ],
                },
                {
                    "name": "gender",
                    "label": "Gender",
                    "control": "select",
                    "default": "",
                    "options": [
                        {"value": "", "label": "Unspecified"},
                        {"value": Gender.MALE.value, "label": Gender.MALE.value},
                        {"value": Gender.FEMALE.value, "label": Gender.FEMALE.value},
                        {"value": Gender.OTHER.value, "label": Gender.OTHER.value},
                        {"value": Gender.UNKNOWN.value, "label": Gender.UNKNOWN.value},
                    ],
                },
                {
                    "name": "product",
                    "label": "Product",
                    "control": "lookup",
                    "lookup_object": "Product",
                    "default": "",
                    "placeholder": "Search Product...",
                },
                {
                    "name": "model",
                    "label": "Model",
                    "control": "lookup",
                    "lookup_object": "Model",
                    "default": "",
                    "placeholder": "Search Model...",
                },
                {
                    "name": "brand",
                    "label": "Brand",
                    "control": "lookup",
                    "lookup_object": "Brand",
                    "default": "",
                    "placeholder": "Search Brand...",
                },
                {"name": "description", "label": "Description", "control": "textarea", "default": ""},
            ],
        },
        "contact": {
            "title_create": "Create Contact",
            "title_edit": "Edit Contact",
            "submit_create": "Create Contact",
            "submit_edit": "Save Contact",
            "fields": [
                {"name": "first_name", "label": "First Name", "control": "text", "default": ""},
                {"name": "last_name", "label": "Last Name", "control": "text", "default": "", "required": True},
                {"name": "email", "label": "Email", "control": "email", "default": ""},
                {"name": "phone", "label": "Phone", "control": "tel", "default": ""},
                {
                    "name": "status",
                    "label": "Status",
                    "control": "select",
                    "default": "New",
                    "required": True,
                    "options": [
                        {"value": "New", "label": "New"},
                        {"value": "Contacted", "label": "Contacted"},
                        {"value": "Qualified", "label": "Qualified"},
                        {"value": "Junk", "label": "Junk"},
                    ],
                },
                {
                    "name": "gender",
                    "label": "Gender",
                    "control": "select",
                    "default": "",
                    "options": [
                        {"value": "", "label": "Unspecified"},
                        {"value": Gender.MALE.value, "label": Gender.MALE.value},
                        {"value": Gender.FEMALE.value, "label": Gender.FEMALE.value},
                        {"value": Gender.OTHER.value, "label": Gender.OTHER.value},
                        {"value": Gender.UNKNOWN.value, "label": Gender.UNKNOWN.value},
                    ],
                },
                {"name": "website", "label": "Website", "control": "text", "default": ""},
                {
                    "name": "tier",
                    "label": "Tier",
                    "control": "select",
                    "default": "Bronze",
                    "options": [
                        {"value": "Bronze", "label": "Bronze"},
                        {"value": "Silver", "label": "Silver"},
                        {"value": "Gold", "label": "Gold"},
                        {"value": "Platinum", "label": "Platinum"},
                    ],
                },
                {"name": "description", "label": "Description", "control": "textarea", "default": ""},
            ],
        },
        "opportunity": {
            "title_create": "Create Opportunity",
            "title_edit": "Edit Opportunity",
            "submit_create": "Create Opportunity",
            "submit_edit": "Save Opportunity",
            "fields": [
                {"name": "name", "label": "Name", "control": "text", "default": "", "required": True},
                {"name": "amount", "label": "Amount", "control": "number", "default": "", "required": True},
                {
                    "name": "stage",
                    "label": "Stage",
                    "control": "select",
                    "default": OpportunityStage.PROSPECTING.value,
                    "required": True,
                    "options": [
                        {"value": OpportunityStage.PROSPECTING.value, "label": OpportunityStage.PROSPECTING.value},
                        {"value": OpportunityStage.QUALIFICATION.value, "label": OpportunityStage.QUALIFICATION.value},
                        {"value": OpportunityStage.TEST_DRIVE.value, "label": OpportunityStage.TEST_DRIVE.value},
                        {"value": OpportunityStage.VALUE_PROPOSITION.value, "label": OpportunityStage.VALUE_PROPOSITION.value},
                        {"value": OpportunityStage.NEGOTIATION.value, "label": OpportunityStage.NEGOTIATION.value},
                        {"value": OpportunityStage.PROPOSAL.value, "label": OpportunityStage.PROPOSAL.value},
                        {"value": OpportunityStage.CLOSED_WON.value, "label": OpportunityStage.CLOSED_WON.value},
                        {"value": OpportunityStage.CLOSED_LOST.value, "label": OpportunityStage.CLOSED_LOST.value},
                    ],
                },
                {
                    "name": "status",
                    "label": "Status",
                    "control": "select",
                    "default": OpportunityStatus.OPEN.value,
                    "options": [
                        {"value": OpportunityStatus.OPEN.value, "label": OpportunityStatus.OPEN.value},
                        {"value": OpportunityStatus.CLOSED_WON.value, "label": OpportunityStatus.CLOSED_WON.value},
                        {"value": OpportunityStatus.CLOSED_LOST.value, "label": OpportunityStatus.CLOSED_LOST.value},
                    ],
                },
                {"name": "probability", "label": "Probability", "control": "number", "default": 10},
                {"name": "temperature", "label": "Temperature", "control": "text", "default": ""},
            ],
        },
    }

    @classmethod
    def _chat_native_form_config(cls, object_type: str) -> Dict[str, Any]:
        return cls.CHAT_NATIVE_FORM_CONFIG[object_type]

    @classmethod
    def _chat_native_form_values(
        cls,
        object_type: str,
        *,
        record: Optional[Any] = None,
        submitted_values: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        config = cls._chat_native_form_config(object_type)
        values: Dict[str, Any] = {}
        submitted_values = submitted_values or {}
        for field in config["fields"]:
            name = field["name"]
            if name in submitted_values:
                values[name] = submitted_values.get(name)
            elif record is not None:
                values[name] = getattr(record, name, field.get("default", ""))
            else:
                values[name] = field.get("default", "")
        return values

    @staticmethod
    def _safe_lookup_display(fetcher, db: Optional[Session], record_id: Optional[str], attr: str = "name") -> str:
        if not record_id:
            return ""
        try:
            record = fetcher(db, record_id)
        except Exception:
            return ""
        return str(getattr(record, attr, "") or "")

    @classmethod
    def _lead_lookup_display_values(
        cls,
        db: Optional[Session],
        values: Dict[str, Any],
    ) -> Dict[str, str]:
        from web.backend.app.services.product_service import ProductService

        return {
            "product": cls._safe_lookup_display(ProductService.get_product, db, values.get("product")),
            "model": cls._safe_lookup_display(ModelService.get_model, db, values.get("model")),
            "brand": cls._safe_lookup_display(VehicleSpecService.get_vehicle_spec, db, values.get("brand")),
        }

    @classmethod
    def _build_chat_native_form_response(
        cls,
        *,
        object_type: str,
        mode: str,
        db: Optional[Session] = None,
        language_preference: Optional[str],
        record: Optional[Any] = None,
        record_id: Optional[str] = None,
        submitted_values: Optional[Dict[str, Any]] = None,
        field_errors: Optional[Dict[str, str]] = None,
        form_error: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        config = cls._chat_native_form_config(object_type)
        values = cls._chat_native_form_values(object_type, record=record, submitted_values=submitted_values)
        display_title = cls._phase1_display_title(object_type, record) if record is not None else None
        title = config["title_create"] if mode == "create" else f"{config['title_edit']} {display_title or record_id or ''}".strip()
        submit_label = config["submit_create"] if mode == "create" else config["submit_edit"]
        is_korean = (language_preference or "").lower() == "kor"
        text = (
            f"{object_type.replace('_', ' ').title()} {'생성' if mode == 'create' else '수정'} 폼을 대화 안에 열었습니다."
            if is_korean else
            f"I opened the {object_type.replace('_', ' ')} {mode} form here in chat."
        )
        lookup_display_values = cls._lead_lookup_display_values(db, values) if object_type == "lead" else {}
        schema_fields: List[Dict[str, Any]] = []
        for field in config["fields"]:
            schema_field = {
                "name": field["name"],
                "label": field["label"],
                "control": field["control"],
                "required": bool(field.get("required")),
                "value": values.get(field["name"]),
            }
            if field.get("placeholder") is not None:
                schema_field["placeholder"] = field["placeholder"]
            if "options" in field:
                schema_field["options"] = field["options"]
            if field["control"] == "lookup":
                schema_field["lookup_object"] = field.get("lookup_object")
                schema_field["display_value"] = lookup_display_values.get(field["name"], "")
            if field_errors and field["name"] in field_errors:
                schema_field["error"] = field_errors[field["name"]]
            schema_fields.append(schema_field)

        form_id_suffix = record_id or conversation_id or "session"
        form = build_chat_native_form(
            form_id=f"{object_type}:{mode}:{form_id_suffix}",
            object_type=object_type,
            mode=mode,
            record_id=record_id,
            title=title,
            description="Fill in the fields below, then save.",
            submit_label=submit_label,
            cancel_label="Cancel",
            required_fields=cls._phase1_required_fields(object_type),
            fields=schema_fields,
            field_errors=field_errors,
            form_error=form_error,
        )
        return {
            "intent": "OPEN_FORM",
            "object_type": object_type,
            "record_id": record_id,
            "form_url": cls._phase1_form_url(object_type, record_id),
            "form_title": title,
            "form_kind": f"{object_type}_{mode}",
            "text": text,
            "form": form,
            "score": 1.0,
        }

    @classmethod
    def _coerce_chat_form_values(cls, object_type: str, values: Dict[str, Any]) -> Dict[str, Any]:
        allowed = {field["name"]: field for field in cls._chat_native_form_config(object_type)["fields"]}
        cleaned: Dict[str, Any] = {}
        for key, value in (values or {}).items():
            if key not in allowed:
                continue
            if isinstance(value, str):
                value = value.strip()
            if value == "":
                value = None
            if key in {"amount", "probability"} and value is not None:
                if isinstance(value, str):
                    value = value.replace(",", "")
                value = int(value)
            cleaned[key] = value
        return cleaned

    @classmethod
    def _validate_chat_form_submission(
        cls,
        object_type: str,
        values: Dict[str, Any],
    ) -> Dict[str, str]:
        field_errors: Dict[str, str] = {}
        allowed = {field["name"]: field for field in cls._chat_native_form_config(object_type)["fields"]}
        required_fields = cls._phase1_required_fields(object_type)

        for field_name in required_fields:
            if values.get(field_name) in (None, ""):
                field_errors[field_name] = "This field is required."

        for field_name, field in allowed.items():
            if field.get("control") == "select" and values.get(field_name) not in (None, ""):
                allowed_values = {option["value"] for option in field.get("options", [])}
                if values[field_name] not in allowed_values:
                    field_errors[field_name] = "Select a valid option."

        if "probability" in values and values.get("probability") is not None:
            probability = values["probability"]
            if probability < 0 or probability > 100:
                field_errors["probability"] = "Probability must be between 0 and 100."

        return field_errors

    @classmethod
    async def submit_chat_native_form(
        cls,
        db: Session,
        *,
        object_type: str,
        mode: str,
        values: Dict[str, Any],
        conversation_id: Optional[str] = None,
        language_preference: Optional[str] = None,
        record_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if object_type not in cls.CHAT_NATIVE_FORM_OBJECTS:
            return {"intent": "CHAT", "text": f"{object_type} chat forms are not supported in this phase."}
        if mode not in {"create", "edit"}:
            return {"intent": "CHAT", "text": "Unsupported form mode."}

        try:
            cleaned_values = cls._coerce_chat_form_values(object_type, values)
        except (TypeError, ValueError):
            target_record = cls._get_phase1_record(db, object_type, record_id) if mode == "edit" and record_id else None
            return cls._build_chat_native_form_response(
                object_type=object_type,
                mode=mode,
                db=db,
                record=target_record,
                record_id=record_id,
                submitted_values=values,
                field_errors={"amount": "Enter a valid number.", "probability": "Enter a valid number."},
                form_error="Review the highlighted fields and try again.",
                conversation_id=conversation_id,
                language_preference=language_preference,
            )

        field_errors = cls._validate_chat_form_submission(object_type, cleaned_values)
        if field_errors:
            target_record = cls._get_phase1_record(db, object_type, record_id) if mode == "edit" and record_id else None
            return cls._build_chat_native_form_response(
                object_type=object_type,
                mode=mode,
                db=db,
                record=target_record,
                record_id=record_id,
                submitted_values=cleaned_values,
                field_errors=field_errors,
                form_error="Review the highlighted fields and try again.",
                conversation_id=conversation_id,
                language_preference=language_preference,
            )

        if object_type == "lead":
            cleaned_values = cls._normalize_lead_lookup_inputs(db, cleaned_values)

        if mode == "create":
            if object_type == "lead":
                record = LeadService.create_lead(db, **cleaned_values)
            elif object_type == "contact":
                record = ContactService.create_contact(db, **cleaned_values)
            else:
                record = OpportunityService.create_opportunity(db, **cleaned_values)
            if not record:
                return cls._build_chat_native_form_response(
                    object_type=object_type,
                    mode=mode,
                    db=db,
                    submitted_values=cleaned_values,
                    form_error=f"I couldn't create that {object_type}.",
                    conversation_id=conversation_id,
                    language_preference=language_preference,
                )
            return cls._build_phase1_open_record_response(
                db,
                object_type,
                record,
                conversation_id,
                "create",
                language_preference,
            )

        if not record_id:
            return {"intent": "CHAT", "text": f"I need the {object_type} record ID before I can save changes."}

        if object_type == "lead":
            record = LeadService.update_lead(db, record_id, **cleaned_values)
        elif object_type == "contact":
            record = ContactService.update_contact(db, record_id, **cleaned_values)
        else:
            record = OpportunityService.update_opportunity(db, record_id, **cleaned_values)

        if not record:
            return {"intent": "CHAT", "text": f"I couldn't find that {object_type} record."}
        return cls._build_phase1_open_record_response(
            db,
            object_type,
            record,
            conversation_id,
            "update",
            language_preference,
        )

    @classmethod
    def _resolve_phase1_object(cls, normalized_query: str) -> Optional[str]:
        for key, value in IntentPreClassifier.OBJECT_MAP.items():
            if value in cls.PHASE1_OBJECTS and key in normalized_query:
                return value
        return None

    @staticmethod
    def _extract_record_id(text: str) -> Optional[str]:
        match = re.search(r"\b([A-Za-z0-9]{15,18}|[A-Za-z]+-[A-Za-z0-9-]+)\b", text)
        return match.group(1) if match else None

    @classmethod
    def _extract_phase1_record_id(cls, user_query: str, object_type: str) -> Optional[str]:
        explicit = cls._extract_record_id(user_query)
        if explicit:
            return explicit

        alias_candidates = [key for key, value in IntentPreClassifier.OBJECT_MAP.items() if value == object_type]
        alias_pattern = "|".join(sorted((re.escape(alias) for alias in alias_candidates), key=len, reverse=True))
        match = re.search(rf"(?:{alias_pattern})\s+([A-Za-z][A-Za-z0-9-]{{3,}})", user_query, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _match_field_value(text: str, aliases: List[str], stop_words: List[str]) -> Optional[str]:
        alias_pattern = "|".join(re.escape(alias) for alias in aliases)
        stop_pattern = "|".join(re.escape(word) for word in stop_words)
        pattern = rf"(?:{alias_pattern})\s*(?:is|to|=|:)?\s*(.+?)(?=\s+(?:{stop_pattern})\b|,|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        value = match.group(1).strip().strip(".,")
        return value or None

    @classmethod
    def _extract_contact_fields_from_text(cls, user_query: str) -> Dict[str, Any]:
        data = {}
        lead_like = cls._extract_lead_update_fields_from_text(user_query)
        for key in ("first_name", "last_name", "status", "email", "phone", "gender", "description"):
            if key in lead_like:
                data[key] = lead_like[key]

        stop_words = [
            "last name",
            "first name",
            "status",
            "email",
            "phone",
            "gender",
            "website",
            "tier",
            "description",
            "desc",
            "note",
        ]
        first_name = cls._match_field_value(user_query, ["first name", "firstname"], stop_words)
        if first_name:
            data["first_name"] = first_name
        gender = cls._match_field_value(user_query, ["gender", "성별"], stop_words)
        if gender:
            data["gender"] = gender
        website = cls._match_field_value(user_query, ["website", "site"], stop_words)
        if website:
            data["website"] = website
        tier = cls._match_field_value(user_query, ["tier"], stop_words)
        if tier:
            data["tier"] = tier

        return data

    @classmethod
    def _extract_opportunity_fields_from_text(cls, user_query: str) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        stop_words = ["name", "stage", "amount", "probability", "status"]

        name = cls._match_field_value(user_query, ["name"], stop_words)
        if name:
            data["name"] = name

        stage = cls._match_field_value(user_query, ["stage"], stop_words)
        if stage:
            data["stage"] = stage

        status = cls._match_field_value(user_query, ["status"], stop_words)
        if status:
            data["status"] = status

        probability_match = re.search(r"probability\s*(?:is|to|=|:)?\s*(\d+)", user_query, re.IGNORECASE)
        if probability_match:
            data["probability"] = int(probability_match.group(1))

        amount_match = re.search(r"amount\s*(?:is|to|=|:)?\s*[₩$]?\s*([\d,]+)", user_query, re.IGNORECASE)
        if amount_match:
            data["amount"] = int(amount_match.group(1).replace(",", ""))

        return data

    @classmethod
    def _extract_phase1_fields(cls, object_type: str, user_query: str) -> Dict[str, Any]:
        if object_type == "lead":
            return cls._extract_lead_update_fields_from_text(user_query)
        if object_type == "contact":
            return cls._extract_contact_fields_from_text(user_query)
        if object_type == "opportunity":
            return cls._extract_opportunity_fields_from_text(user_query)
        return {}

    @classmethod
    def _phase1_required_fields(cls, object_type: str) -> List[str]:
        mapping = {
            "lead": ["last_name", "status"],
            "contact": ["last_name", "status"],
            "opportunity": ["name", "stage", "amount"],
        }
        return mapping.get(object_type, [])

    @classmethod
    def _has_explicit_phase1_field_hints(cls, object_type: str, user_query: str) -> bool:
        normalized = IntentPreClassifier.normalize(user_query)
        if object_type in {"lead", "contact"}:
            hints = [
                "first name",
                "last name",
                "email",
                "phone",
                "status",
                "gender",
                "website",
                "tier",
                "description",
                "desc",
                "note",
                ":",
            ]
            if any(hint in normalized or hint in user_query for hint in hints):
                return True
            if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", user_query):
                return True
            if re.search(r"(?:\+?\d[\d\-\s]{7,}\d)", user_query):
                return True
            return False
        if object_type == "opportunity":
            return any(hint in normalized or hint in user_query for hint in ["name", "stage", "amount", "probability", "status", ":"])
        return False

    @classmethod
    def _phase1_form_url(cls, object_type: str, record_id: Optional[str] = None) -> str:
        plural = {
            "lead": "leads",
            "contact": "contacts",
            "opportunity": "opportunities",
        }[object_type]
        base = f"/{plural}/new-modal"
        return f"{base}?id={record_id}" if record_id else base

    @classmethod
    def _phase1_display_title(cls, object_type: str, record: Any) -> str:
        if object_type == "lead":
            return cls._lead_name(record)
        if object_type == "contact":
            name = " ".join(
                part for part in [getattr(record, "first_name", None), getattr(record, "last_name", None)] if part
            ).strip()
            return name or getattr(record, "name", None) or str(getattr(record, "id", "Unnamed Contact"))
        if object_type == "opportunity":
            return getattr(record, "name", None) or str(getattr(record, "id", "Unnamed Opportunity"))
        return str(getattr(record, "id", "Record"))

    @classmethod
    def _build_contact_chat_card(cls, contact: Any) -> Dict[str, Any]:
        return {
            "type": "record_paste",
            "object_type": "contact",
            "title": cls._phase1_display_title("contact", contact),
            "record_id": str(getattr(contact, "id", "")),
            "fields": [
                {"label": "First name", "value": cls._display_value(getattr(contact, "first_name", None))},
                {"label": "Last name", "value": cls._display_value(getattr(contact, "last_name", None))},
                {"label": "Email", "value": cls._display_value(getattr(contact, "email", None))},
                {"label": "Phone", "value": cls._display_value(getattr(contact, "phone", None))},
                {"label": "Status", "value": cls._display_value(getattr(contact, "status", None))},
            ],
        }

    @classmethod
    def _build_opportunity_chat_card(cls, opportunity: Any) -> Dict[str, Any]:
        return {
            "type": "record_paste",
            "object_type": "opportunity",
            "title": cls._phase1_display_title("opportunity", opportunity),
            "record_id": str(getattr(opportunity, "id", "")),
            "fields": [
                {"label": "Name", "value": cls._display_value(getattr(opportunity, "name", None))},
                {"label": "Stage", "value": cls._display_value(getattr(opportunity, "stage", None))},
                {"label": "Amount", "value": cls._display_value(getattr(opportunity, "amount", None))},
                {"label": "Probability", "value": cls._display_value(getattr(opportunity, "probability", None))},
                {"label": "Status", "value": cls._display_value(getattr(opportunity, "status", None))},
            ],
        }

    @classmethod
    def _build_phase1_open_record_response(
        cls,
        db: Optional[Session],
        object_type: str,
        record: Any,
        conversation_id: Optional[str],
        action: str,
        language_preference: Optional[str],
    ) -> Dict[str, Any]:
        record_id = str(getattr(record, "id", ""))
        if object_type == "lead":
            return cls._build_lead_open_record_response(
                db=db,
                lead=record,
                conversation_id=conversation_id,
                action=action,
                language_preference=language_preference,
            )

        redirect_url = {
            "contact": f"/contacts/{record_id}",
            "opportunity": f"/opportunities/{record_id}",
        }[object_type]
        chat_card = None
        if object_type == "contact":
            chat_card = cls._build_contact_chat_card(record)
        elif object_type == "opportunity":
            chat_card = cls._build_opportunity_chat_card(record)

        return build_object_open_record_response(
            object_type=object_type,
            record_id=record_id,
            redirect_url=redirect_url,
            title=cls._phase1_display_title(object_type, record),
            action=action,
            conversation_id=conversation_id,
            language_preference=language_preference,
            chat_card=chat_card,
        )

    @classmethod
    def _build_phase1_edit_form_response(
        cls,
        object_type: str,
        record: Any,
        language_preference: Optional[str],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        record_id = str(getattr(record, "id", ""))
        if object_type in cls.CHAT_NATIVE_FORM_OBJECTS:
            return cls._build_chat_native_form_response(
                object_type=object_type,
                mode="edit",
                db=db,
                record=record,
                record_id=record_id,
                conversation_id=None,
                language_preference=language_preference,
            )
        return build_object_edit_form_response(
            object_type=object_type,
            record_id=record_id,
            form_url=cls._phase1_form_url(object_type, record_id),
            title=f"Edit {cls._phase1_display_title(object_type, record)}",
            language_preference=language_preference,
        )

    @classmethod
    def _get_phase1_record(cls, db: Session, object_type: str, record_id: str) -> Any:
        if object_type == "lead":
            return LeadService.get_lead(db, record_id)
        if object_type == "contact":
            return ContactService.get_contact(db, record_id)
        if object_type == "opportunity":
            return OpportunityService.get_opportunity(db, record_id)
        return None

    @classmethod
    def _resolve_phase1_deterministic_request(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        language_preference: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        object_type = cls._resolve_phase1_object(normalized)
        if not object_type:
            return None

        explicit_record_id = cls._extract_phase1_record_id(user_query, object_type)
        has_create = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_CREATE_ACTIONS))
        has_update = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_UPDATE_ACTIONS))
        has_query = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_QUERY_ACTIONS))
        has_read = IntentPreClassifier._contains_action(normalized, list(cls.GENERIC_READ_ACTIONS))
        has_recent_query = any(marker in normalized for marker in cls.RECENT_QUERY_MARKERS)

        if has_query and object_type in cls.PHASE1_OBJECTS:
            if "all" in normalized or "show all" in normalized or "list" in normalized or object_type == "opportunity" or has_recent_query:
                query_data = {"query_mode": "recent"} if has_recent_query else {}
                return {
                    "intent": "QUERY",
                    "object_type": object_type,
                    "data": query_data,
                    "score": 1.0,
                }

        if has_create and object_type in cls.PHASE1_OBJECTS:
            if not cls._has_explicit_phase1_field_hints(object_type, user_query):
                return cls._build_chat_native_form_response(
                    object_type=object_type,
                    mode="create",
                    submitted_values={},
                    conversation_id=conversation_id,
                    language_preference=language_preference,
                )
            data = cls._extract_phase1_fields(object_type, user_query)
            required_fields = cls._phase1_required_fields(object_type)
            if all(field in data and data[field] not in (None, "") for field in required_fields):
                return {
                    "intent": "CREATE",
                    "object_type": object_type,
                    "data": data,
                    "score": 1.0,
                    "language_preference": language_preference,
                }
            return cls._build_chat_native_form_response(
                object_type=object_type,
                mode="create",
                submitted_values=data,
                conversation_id=conversation_id,
                language_preference=language_preference,
            )

        if (has_update or has_read) and object_type in cls.PHASE1_OBJECTS and explicit_record_id:
            if has_update:
                data = cls._extract_phase1_fields(object_type, user_query)
                if data:
                    return {
                        "intent": "UPDATE",
                        "object_type": object_type,
                        "record_id": explicit_record_id,
                        "data": data,
                        "score": 1.0,
                        "language_preference": language_preference,
                    }
                return {
                    "intent": "OPEN_FORM",
                    "object_type": object_type,
                    "record_id": explicit_record_id,
                    "form_url": cls._phase1_form_url(object_type, explicit_record_id),
                    "score": 1.0,
                    "language_preference": language_preference,
                }
            return {
                "intent": "MANAGE",
                "object_type": object_type,
                "record_id": explicit_record_id,
                "score": 1.0,
                "language_preference": language_preference,
            }

        if has_update and object_type in cls.PHASE1_OBJECTS:
            return {
                "intent": "CHAT",
                "object_type": object_type,
                "text": f"I can update that {object_type}, but I need the record ID first.",
                "score": 1.0,
            }

        return None

    @classmethod
    def _extract_ranked_query_index(cls, user_query: str) -> Optional[int]:
        normalized = IntentPreClassifier.normalize(user_query)
        for marker, index in cls.ORDINAL_MARKERS:
            if marker in normalized:
                return index
        return None

    @classmethod
    def _resolve_contextual_query_reference(
        cls,
        user_query: str,
        conversation_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(user_query)
        ranked_index = cls._extract_ranked_query_index(user_query)
        if ranked_index is None:
            return None
        follow_up_markers = (
            "one",
            "record",
            "result",
            "item",
            "that",
            "this",
            "it",
            "them",
            "those",
            "그",
            "이",
            "해당",
        )
        explicit_ordinal_markers = (
            "first",
            "1st",
            "second",
            "2nd",
            "third",
            "3rd",
            "fourth",
            "4th",
            "fifth",
            "5th",
        )
        if not any(marker in normalized for marker in follow_up_markers) and not any(
            marker in normalized for marker in explicit_ordinal_markers
        ):
            return None

        manage_markers = list(cls.GENERIC_READ_ACTIONS | cls.GENERIC_UPDATE_ACTIONS)
        if not IntentPreClassifier._contains_action(normalized, manage_markers):
            return None

        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if value in cls.PHASE1_OBJECTS and key in normalized
        ]
        desired_object_type = explicit_objects[0] if explicit_objects else None
        query_context = ConversationContextStore.get_query_results(conversation_id)
        query_object_type = query_context.get("object_type")
        ranked_results = list(query_context.get("results") or [])

        if query_object_type not in cls.PHASE1_OBJECTS or not ranked_results:
            object_hint = desired_object_type or "record"
            return {
                "intent": "CHAT",
                "object_type": desired_object_type,
                "text": (
                    f"I need a recent {object_hint} list first. Try `show recent {object_hint}s` "
                    "or `show all contacts`, then tell me which one to open or edit."
                ),
                "score": 1.0,
            }

        if desired_object_type and desired_object_type != query_object_type:
            return {
                "intent": "CHAT",
                "object_type": desired_object_type,
                "text": (
                    f"Your most recent list shows {query_object_type}s, not {desired_object_type}s. "
                    f"Show {desired_object_type}s first, then tell me which one to open or edit."
                ),
                "score": 1.0,
            }

        if ranked_index >= len(ranked_results):
            return {
                "intent": "CHAT",
                "object_type": query_object_type,
                "text": (
                    f"I only have {len(ranked_results)} {query_object_type} result"
                    f"{'' if len(ranked_results) == 1 else 's'} in the most recent list. "
                    "Tell me a valid position or show a longer list first."
                ),
                "score": 1.0,
            }

        chosen = ranked_results[ranked_index]
        return {
            "intent": "MANAGE",
            "object_type": query_object_type,
            "record_id": chosen["record_id"],
            "score": 1.0,
        }

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
            "first_name": [r"first name\s*(?:is|to|=|:)?\s*([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)이름(?:은|는|을|를)?\s+([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)"],
            "last_name": [r"last name\s*(?:is|to|=|:)?\s*([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)성(?:은|는|을|를)?\s+([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)"],
            "gender": [r"gender\s*(?:is|to|=|:)?\s*([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)성별(?:은|는|을|를)?\s+([A-Za-z가-힣\s-]+?)(?:,|and|그리고|$)"],
            "brand": [r"brand\s*(?:is|to|=|:)?\s*([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)브랜드(?:는|은|를|을)?\s+([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)"],
            "model": [r"model\s*(?:is|to|=|:)?\s*([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)모델(?:은|는|을|를)?\s+([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)"],
            "product": [r"product\s*(?:is|to|=|:)?\s*([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)", r"(?:^|\s)상품(?:은|는|을|를)?\s+([A-Za-z0-9가-힣\s-]+?)(?:,|and|그리고|$)"],
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

    @classmethod
    def _resolve_explicit_lead_record_request(
        cls,
        user_query: str,
        language_preference: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        match = re.match(
            r"^\s*(show|open|view|read|details|manage|edit|update|change|modify|delete|remove|erase|보여|보여줘|열어|열어줘|상세|관리|수정|변경|바꿔|삭제)\s+"
            r"(?:this\s+|that\s+)?(lead|leads|리드|리드를)\s+"
            r"([A-Za-z0-9]{15,18}|[A-Za-z]+-[A-Za-z0-9-]+)"
            r"(?:[\s,:-]+(.*?))?\s*$",
            user_query,
            re.IGNORECASE,
        )
        if not match:
            return None

        action = (match.group(1) or "").lower()
        record_id = match.group(3)
        trailing_text = (match.group(4) or "").strip()

        if action in cls.LEAD_READ_ACTIONS:
            return {
                "intent": "MANAGE",
                "object_type": "lead",
                "record_id": record_id,
                "score": 1.0,
                "language_preference": language_preference,
            }

        if action in cls.LEAD_EDIT_ACTIONS:
            return {
                "intent": "OPEN_FORM",
                "object_type": "lead",
                "record_id": record_id,
                "form_url": f"/leads/new-modal?id={record_id}",
                "score": 1.0,
                "language_preference": language_preference,
            }

        if action in cls.LEAD_UPDATE_ACTIONS:
            update_source = trailing_text or user_query
            data = cls._extract_lead_update_fields_from_text(update_source)
            if not data:
                return {
                    "intent": "OPEN_FORM",
                    "object_type": "lead",
                    "record_id": record_id,
                    "form_url": f"/leads/new-modal?id={record_id}",
                    "score": 1.0,
                    "language_preference": language_preference,
                }
            return {
                "intent": "UPDATE",
                "object_type": "lead",
                "record_id": record_id,
                "data": data,
                "score": 1.0,
                "language_preference": language_preference,
            }

        if action in cls.LEAD_DELETE_ACTIONS:
            return {
                "intent": "DELETE",
                "object_type": "lead",
                "record_id": record_id,
                "score": 1.0,
                "language_preference": language_preference,
            }

        return None

    @classmethod
    def _resolve_quick_lead_form_request(
        cls,
        db: Session,
        user_query: str,
        conversation_id: Optional[str],
        language_preference: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        if explicit_objects and "lead" not in explicit_objects:
            return None

        if "lead" not in normalized_query and "리드" not in user_query:
            return None

        has_explicit_id = bool(re.search(r"\b([A-Za-z0-9]{15,18}|[A-Za-z]+-[A-Za-z0-9-]+)\b", user_query))
        if has_explicit_id:
            return None

        extracted_create_data = cls._extract_lead_fields_from_text(user_query)
        if any(token in normalized_query for token in cls.LEAD_CREATE_ACTIONS) and not extracted_create_data:
            return cls._build_lead_create_form_response(language_preference)

        if any(token in normalized_query for token in cls.LEAD_EDIT_ACTIONS | cls.LEAD_UPDATE_ACTIONS):
            context = ConversationContextStore.get_context(conversation_id)
            if context.get("last_object") != "lead" or not context.get("last_record_id"):
                return None
            lead = LeadService.get_lead(db, context["last_record_id"])
            if not lead:
                return None
            return cls._build_phase1_edit_form_response(
                "lead",
                lead,
                language_preference,
                db=db,
            )

        return None

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
            return ""
        if hasattr(value, "value"):
            return str(value.value)
        if isinstance(value, bool):
            return "Yes" if value else "No"
        return str(value)

    @staticmethod
    def _looks_like_record_id(value: Any) -> bool:
        if not value or not isinstance(value, str):
            return False
        return bool(re.fullmatch(r"[A-Za-z]+-[A-Za-z0-9-]+", value) or re.fullmatch(r"[A-Za-z0-9]{15,18}", value))

    @classmethod
    def _resolve_lookup_name_to_id(cls, db: Session, lookup_type: str, raw_value: Any) -> Any:
        value = cls._display_value(raw_value).strip()
        if not value or cls._looks_like_record_id(value):
            return raw_value

        if lookup_type == "brand":
            record = (
                db.query(VehicleSpecification)
                .filter(
                    VehicleSpecification.deleted_at == None,
                    VehicleSpecification.record_type == "Brand",
                    VehicleSpecification.name.ilike(value),
                )
                .first()
            )
            return record.id if record else raw_value

        if lookup_type == "model":
            record = db.query(DbModel).filter(DbModel.deleted_at == None, DbModel.name.ilike(value)).first()
            return record.id if record else raw_value

        if lookup_type == "product":
            record = db.query(DbProduct).filter(DbProduct.deleted_at == None, DbProduct.name.ilike(value)).first()
            return record.id if record else raw_value

        return raw_value

    @classmethod
    def _normalize_lead_lookup_inputs(cls, db: Session, data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        normalized = dict(data or {})
        for field in ("brand", "model", "product"):
            if field in normalized:
                normalized[field] = cls._resolve_lookup_name_to_id(db, field, normalized.get(field))
        return normalized

    @staticmethod
    def _lead_name(lead: Any) -> str:
        name = " ".join(
            part for part in [getattr(lead, "first_name", None), getattr(lead, "last_name", None)] if part
        ).strip()
        if not name or name == "-":
            return str(getattr(lead, "id", "Unnamed Lead"))
        return name

    @classmethod
    def _lead_delete_summary(cls, lead: Any) -> str:
        name = cls._lead_name(lead)
        phone = cls._display_value(getattr(lead, "phone", None))
        if phone:
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
        return cls._build_chat_native_form_response(
            object_type="lead",
            mode="create",
            language_preference=language_preference,
        )

    @classmethod
    def _build_lead_edit_form_response(
        cls,
        record_id: str,
        lead_name: str,
        language_preference: Optional[str],
    ) -> Dict[str, Any]:
        return build_lead_edit_form_response(record_id, lead_name, language_preference)

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
                {"label": "Open Record", "action": "open", "tone": "primary"},
                {"label": "Edit", "action": "edit", "tone": "secondary"},
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

    @classmethod
    def _build_lead_open_record_response(
        cls,
        db: Session,
        lead: Any,
        conversation_id: Optional[str],
        action: str,
        language_preference: Optional[str],
    ) -> Dict[str, Any]:
        return build_lead_open_record_response(
            db=db,
            lead=lead,
            conversation_id=conversation_id,
            action=action,
            language_preference=language_preference,
            build_chat_card=cls._build_lead_chat_card,
            lead_name_getter=cls._lead_name,
        )

    @classmethod
    def _build_phase1_query_sql(cls, obj: str, data: Dict[str, Any]) -> Optional[str]:
        config = cls._default_query_parts(obj)
        if not config:
            return None

        if obj == "opportunity" and data.get("query_mode") == "recent":
            return (
                f"SELECT {config['select']} FROM {config['from']} "
                f"WHERE {config['where']} ORDER BY {config['order_by']}"
            )

        return (
            f"SELECT {config['select']} FROM {config['from']} "
            f"WHERE {config['where']} ORDER BY {config['order_by']}"
        )

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
                "select": "l.id, TRIM(CONCAT_WS(' ', l.first_name, l.last_name)) AS display_name, l.phone, l.status, COALESCE(m.name, l.model) AS model, l.created_at",
                "from": "leads l LEFT JOIN models m ON l.model = m.id",
                "where": "l.deleted_at IS NULL",
                "order_by": "l.created_at DESC",
            },
            "contact": {
                "select": "c.id, TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) AS display_name, c.phone, c.email, c.tier, c.created_at",
                "from": "contacts c",
                "where": "c.deleted_at IS NULL",
                "order_by": "c.created_at DESC",
            },
            "opportunity": {
                "select": "o.id, o.name, TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) AS contact_display_name, c.phone AS contact_phone, o.stage, o.amount, COALESCE(m.name, o.model) AS model",
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
                "select": "m.id, m.name, vs.name AS brand, m.description",
                "from": "models m LEFT JOIN vehicle_specifications vs ON m.brand = vs.id",
                "where": "m.deleted_at IS NULL",
                "order_by": "m.created_at DESC",
            },
            "product": {
                "select": "p.id, p.name, vs.name AS brand, m.name AS model, p.category, p.base_price",
                "from": "products p LEFT JOIN vehicle_specifications vs ON p.brand = vs.id LEFT JOIN models m ON p.model = m.id",
                "where": "p.deleted_at IS NULL",
                "order_by": "p.created_at DESC",
            },
            "asset": {
                "select": "a.id, a.vin, a.status, vs.name AS brand, m.name AS model, a.vin AS name",
                "from": "assets a LEFT JOIN vehicle_specifications vs ON a.brand = vs.id LEFT JOIN models m ON a.model = m.id",
                "where": "a.deleted_at IS NULL",
                "order_by": "a.created_at DESC",
            },
            "message_template": {
                "select": "id, name, record_type, subject, content, (image_url IS NOT NULL) AS has_image",
                "from": "message_templates",
                "where": "deleted_at IS NULL",
                "order_by": "created_at DESC",
            },
            "message_send": {
                "select": "ms.id, TRIM(CONCAT_WS(' ', c.first_name, c.last_name)) AS contact, ms.direction, ms.status, ms.sent_at",
                "from": "message_sends ms LEFT JOIN contacts c ON ms.contact = c.id",
                "where": "ms.deleted_at IS NULL",
                "order_by": "ms.sent_at DESC",
            },
        }
        return mapping.get(obj)

    @staticmethod
    def _apply_search_to_sql(obj: str, config: Dict[str, str], term: str) -> Dict[str, str]:
        if not term:
            return config
        
        search_fields = {
            "lead": [
                "TRIM(CONCAT_WS(' ', l.first_name, l.last_name))",
                "l.first_name",
                "l.last_name",
                "l.email",
                "l.phone",
                "l.status",
                "COALESCE(m.name, l.model)",
            ],
            "contact": [
                "TRIM(CONCAT_WS(' ', c.first_name, c.last_name))",
                "c.first_name",
                "c.last_name",
                "c.email",
                "c.phone",
                "c.tier",
            ],
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
    def _resolve_contextual_record_reference(
        cls,
        user_query: str,
        conversation_id: Optional[str],
        selection: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not conversation_id and not selection:
            return None

        context = ConversationContextStore.get_context(conversation_id)
        last_created = context.get("last_created") or {}

        q_low = user_query.lower()

        def contains_marker(marker: str) -> bool:
            if not marker:
                return False
            if re.fullmatch(r"[a-z]+", marker):
                return re.search(rf"\b{re.escape(marker)}\b", q_low) is not None
            return marker in q_low or marker in user_query

        recent_markers = ["just created", "recently created", "방금 생성", "방금 생성한", "방금 만든", "최근 만든", "최근 생성"]
        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if value in cls.PHASE1_OBJECTS and key in normalized_query
        ]
        context_object_type = context.get("last_object") or last_created.get("object_type")
        context_record_id = context.get("last_record_id") or last_created.get("record_id")
        selection_payload = selection or ConversationContextStore.get_selection(conversation_id)
        selection_object_type = (selection_payload or {}).get("object_type")
        selection_ids = list((selection_payload or {}).get("ids") or [])
        selection_record_id = selection_ids[0] if len(selection_ids) == 1 else None

        if context_object_type not in cls.PHASE1_OBJECTS:
            context_object_type = None
            context_record_id = None
        if selection_object_type not in cls.PHASE1_OBJECTS:
            selection_object_type = None
            selection_record_id = None

        if any(contains_marker(marker) for marker in recent_markers):
            recent_object_type = last_created.get("object_type") or context_object_type
            recent_record_id = last_created.get("record_id") or context_record_id
            if not recent_object_type or not recent_record_id:
                return None
            return {
                "intent": "MANAGE",
                "object_type": recent_object_type,
                "record_id": recent_record_id,
                "score": 1.0,
            }

        follow_up_markers = ["that", "this", "it", "them", "those", "that one", "the one", "this one", "the record", "record", "그", "이", "해당", "방금", "최근"]
        has_follow_up_marker = any(contains_marker(marker) for marker in follow_up_markers)
        manage_markers = ["show", "open", "manage", "view", "details", "grab", "fetch", "보여", "열어", "관리", "상세"]
        update_markers = ["update", "edit", "change", "modify", "tweak", "fix", "수정", "변경", "바꿔"]

        if not has_follow_up_marker or not any(contains_marker(marker) for marker in manage_markers + update_markers):
            return None

        desired_object_type = explicit_objects[0] if explicit_objects else None
        context_candidate = (
            {"object_type": context_object_type, "record_id": context_record_id}
            if context_object_type and context_record_id else None
        )
        selection_candidate = (
            {"object_type": selection_object_type, "record_id": selection_record_id}
            if selection_object_type and selection_record_id else None
        )

        if desired_object_type:
            if context_candidate and context_candidate["object_type"] == desired_object_type:
                return {
                    "intent": "MANAGE",
                    "object_type": context_candidate["object_type"],
                    "record_id": context_candidate["record_id"],
                    "score": 1.0,
                }
            if selection_candidate and selection_candidate["object_type"] == desired_object_type:
                return {
                    "intent": "MANAGE",
                    "object_type": selection_candidate["object_type"],
                    "record_id": selection_candidate["record_id"],
                    "score": 1.0,
                }
            return {
                "intent": "CHAT",
                "object_type": desired_object_type,
                "text": f"I need a specific {desired_object_type} record first. Open one or select one, then try again.",
                "score": 1.0,
            }

        if context_candidate and selection_candidate:
            if (
                context_candidate["object_type"] != selection_candidate["object_type"]
                or context_candidate["record_id"] != selection_candidate["record_id"]
            ):
                return {
                    "intent": "CHAT",
                    "text": (
                        f"I found two different records in context: the last {context_candidate['object_type']} "
                        f"({context_candidate['record_id']}) and the selected {selection_candidate['object_type']} "
                        f"({selection_candidate['record_id']}). Tell me which one to open or edit."
                    ),
                    "score": 1.0,
                }

        chosen = context_candidate or selection_candidate
        if chosen:
            return {
                "intent": "MANAGE",
                "object_type": chosen["object_type"],
                "record_id": chosen["record_id"],
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
        is_force_delete = "[force_delete]" in user_query.lower() or "[FORCE_DELETE]" in user_query
        delete_markers = ["delete", "remove", "erase", "nuke", "dump", "삭제"]
        if not any(marker in q_low or marker in user_query for marker in delete_markers):
            return None

        # Improved UUID and Record ID extraction (matches e.g., lead-123 or 550e8400-...)
        explicit_id_match = re.search(r"\b([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b", user_query, re.IGNORECASE)
        if not explicit_id_match:
            explicit_id_match = re.search(r"\b([A-Za-z0-9]{15,18})\b", user_query)
        if not explicit_id_match:
            explicit_id_match = re.search(r"\b([A-Za-z]+-[A-Za-z0-9-]+)\b", user_query)
        explicit_id = explicit_id_match.group(1) if explicit_id_match else None

        selection_payload = selection or ConversationContextStore.get_selection(conversation_id)
        selected_ids = list((selection_payload or {}).get("ids") or [])
        selected_labels = list((selection_payload or {}).get("labels") or [])
        selected_object = (selection_payload or {}).get("object_type")
        
        # If ID was in query and matched an object type, prioritize it
        normalized_query = IntentPreClassifier.normalize(user_query)
        explicit_objects = [
            value for key, value in IntentPreClassifier.OBJECT_MAP.items()
            if key in normalized_query
        ]
        object_type = explicit_objects[0] if explicit_objects else None

        if selected_object and selected_ids:
            if is_force_delete:
                ConversationContextStore.clear_pending_delete(conversation_id)
                return {
                    "intent": "DELETE",
                    "object_type": selected_object,
                    "record_id": selected_ids[0] if len(selected_ids) == 1 else None,
                    "selection": {"object_type": selected_object, "ids": selected_ids},
                    "score": 1.0,
                }
             # ... rest of selection logic
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

        context = ConversationContextStore.get_context(conversation_id)
        if not object_type:
            object_type = context.get("last_object")

        record_id = explicit_id or context.get("last_record_id")
        last_created = context.get("last_created") or {}
        if not record_id:
            record_id = last_created.get("record_id")
        if not object_type:
            object_type = last_created.get("object_type")

        if explicit_objects and object_type and object_type not in explicit_objects:
            return None
        if not object_type or not record_id:
            return None

        # Phase 177: Bypass double confirmation if the user explicitly provided the ID in the query
        # Phase 177/182/183: Bypass double confirmation if force delete or explicit ID
        if is_force_delete or (record_id and (record_id.lower() in user_query.lower() or record_id.lower() in normalized_query.lower())):
             return {
                "intent": "DELETE",
                "object_type": object_type,
                "record_id": record_id,
                "score": 1.0,
            }

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

        explicit_lead_record_resolution = cls._resolve_explicit_lead_record_request(
            user_query,
            language_preference,
        )
        if explicit_lead_record_resolution:
            if explicit_lead_record_resolution["intent"] == "OPEN_FORM":
                lead = LeadService.get_lead(db, explicit_lead_record_resolution["record_id"])
                if not lead:
                    return {"intent": "CHAT", "object_type": "lead", "text": "I couldn't find that lead record."}
                return cls._build_phase1_edit_form_response(
                    "lead",
                    lead,
                    language_preference,
                )
            return await cls._execute_intent(
                db,
                explicit_lead_record_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        pending_edit_resolution = cls._resolve_pending_lead_edit(user_query, conversation_id)
        if pending_edit_resolution:
            # Phase 177: If the query is an explicit "edit lead {id}", open the form directly
            if "edit" in user_query.lower() or "수정" in user_query:
                record_id = pending_edit_resolution.get("record_id")
                if record_id:
                     lead = LeadService.get_lead(db, record_id)
                     if lead:
                         return cls._build_phase1_edit_form_response(
                             "lead",
                             lead,
                             language_preference,
                             db=db,
                         )

            pending_edit_resolution["language_preference"] = language_preference
            return await cls._execute_intent(
                db,
                pending_edit_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        quick_lead_form_resolution = cls._resolve_quick_lead_form_request(
            db,
            user_query,
            conversation_id,
            language_preference,
        )
        if quick_lead_form_resolution:
            return quick_lead_form_resolution

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
            # Phase 177 Fix: If the resolution is already a final intent (DELETE), execute it immediately
            if delete_resolution.get("intent") == "DELETE":
                return await cls._execute_intent(db, delete_resolution, user_query, conversation_id=conversation_id, page=page, per_page=per_page)
            return delete_resolution

        contextual_query_resolution = cls._resolve_contextual_query_reference(user_query, conversation_id)
        if contextual_query_resolution:
            if contextual_query_resolution.get("intent") == "CHAT":
                return contextual_query_resolution
            contextual_query_resolution["language_preference"] = language_preference
            return await cls._execute_intent(
                db,
                contextual_query_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

        explicit_manage_resolution = cls._resolve_explicit_manage_request(user_query)
        if explicit_manage_resolution:
            explicit_manage_resolution["language_preference"] = language_preference
            return await cls._execute_intent(db, explicit_manage_resolution, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        contextual_response = cls._resolve_contextual_record_reference(user_query, conversation_id, selection)
        if contextual_response:
            contextual_response["language_preference"] = language_preference
            return await cls._execute_intent(db, contextual_response, user_query, conversation_id=conversation_id, page=page, per_page=per_page)

        phase1_resolution = cls._resolve_phase1_deterministic_request(
            user_query,
            conversation_id,
            language_preference,
        )
        if phase1_resolution:
            if phase1_resolution.get("intent") == "CHAT":
                return phase1_resolution
            if (
                phase1_resolution.get("intent") == "OPEN_FORM"
                and phase1_resolution.get("object_type") in cls.CHAT_NATIVE_FORM_OBJECTS
            ):
                if phase1_resolution.get("form"):
                    return phase1_resolution
                if phase1_resolution.get("record_id"):
                    record = cls._get_phase1_record(
                        db,
                        phase1_resolution["object_type"],
                        phase1_resolution["record_id"],
                    )
                    if not record:
                        return {"intent": "CHAT", "text": f"I couldn't find that {phase1_resolution['object_type']} record."}
                    return cls._build_phase1_edit_form_response(
                        phase1_resolution["object_type"],
                        record,
                        language_preference,
                        db=db,
                    )
                return cls._build_chat_native_form_response(
                    object_type=phase1_resolution["object_type"],
                    mode="create",
                    conversation_id=conversation_id,
                    language_preference=language_preference,
                )
            return await cls._execute_intent(
                db,
                phase1_resolution,
                user_query,
                conversation_id=conversation_id,
                page=page,
                per_page=per_page,
            )

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
        
        DELETE FLOW:
        - Use intent "DELETE" immediately if the user provides a record ID (e.g., "Delete lead 123") or confirms deletion (e.g., "Yes").
        - The UI already handles final confirmations. Proceed directly to the deletion without asking "Are you sure?" again.
        
        TABLE DATA STANDARDS:
        - For all record displays (QUERY, CREATE, UPDATE, MANAGE): You MUST strictly follow the AGENT_TABLE_SCHEMAS.
        - Leads/Contacts: You MUST use `TRIM(CONCAT_WS(' ', first_name, last_name)) AS display_name`.
        - All lookup fields shown to users MUST use readable names, never raw IDs.
        - Leads/Opportunities/Assets/Products: You MUST JOIN with the `models` table to provide `model` (e.g. GV80) instead of raw UUIDs.
        - Your `SELECT` fields MUST match exactly with the frontend schemas:
          - Lead: display_name, phone, status, model, created_at
          - Contact: display_name, phone, email, tier, created_at
          - Opportunity: name, contact_display_name, contact_phone, stage, amount, model
        - Always return the `id` field in SQL queries as the first column.
        
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
                    timeout=8.0
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
                    timeout=8.0
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
                    timeout=8.0,
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
                    timeout=9.0
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
            if obj in cls.PHASE1_OBJECTS and record_id:
                record = cls._get_phase1_record(db, obj, record_id)
                if not record:
                    return {"intent": "CHAT", "text": f"I couldn't find the {obj} record with ID {record_id}."}
                if cls._detect_manage_mode(user_query) == "edit":
                    return cls._build_phase1_edit_form_response(
                        obj,
                        record,
                        agent_output.get("language_preference"),
                        db=db,
                    )
                return cls._build_phase1_open_record_response(
                    db,
                    obj,
                    record,
                    conversation_id,
                    "manage",
                    agent_output.get("language_preference"),
                )
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
                    if mode == "edit":
                        ConversationContextStore.remember_object(conversation_id, "lead", "MANAGE", record_id=record_id)
                        return cls._build_phase1_edit_form_response(
                            "lead",
                            lead,
                            agent_output.get("language_preference"),
                            db=db,
                        )
                    return cls._build_lead_open_record_response(
                        db,
                        lead,
                        conversation_id,
                        action="manage",
                        language_preference=agent_output.get("language_preference"),
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
                agent_output["text"] = f"I've selected **{record_details}**. \n\nFields you can update:\n{button_html}\n\nWhat would you like to do?{template_image_html}"
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
            if obj in cls.PHASE1_OBJECTS and not sql:
                sql = cls._build_phase1_query_sql(obj, data)
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
                    ConversationContextStore.remember_query_results(conversation_id, obj, paged["results"])
                    return agent_output
                except Exception as e:
                    logger.error(f"SQL Error: {str(e)}")
                    return {"intent": "CHAT", "text": f"Database query failed: {str(e)}"}

        data = cls._clean_data(data)
        
        if intent == "CREATE":
            if obj == "lead":
                data = cls._normalize_lead_lookup_inputs(db, data)
                res = LeadService.create_lead(db, **data)
                if not res:
                    return {"intent": "CHAT", "text": "I encountered an error while creating the lead. Please try again or check the required fields."}
                return cls._build_lead_open_record_response(
                    db,
                    res,
                    conversation_id,
                    action="create",
                    language_preference=agent_output.get("language_preference"),
                )
            elif obj == "contact":
                res = ContactService.create_contact(db, **data)
                if not res:
                    return {"intent": "CHAT", "text": "I encountered an error while creating the contact."}
                return cls._build_phase1_open_record_response(
                    db,
                    "contact",
                    res,
                    conversation_id,
                    "create",
                    agent_output.get("language_preference"),
                )
            elif obj == "opportunity":
                res = OpportunityService.create_opportunity(db, **data)
                if not res:
                    return {"intent": "CHAT", "text": "I encountered an error while creating the opportunity."}
                return cls._build_phase1_open_record_response(
                    db,
                    "opportunity",
                    res,
                    conversation_id,
                    "create",
                    agent_output.get("language_preference"),
                )
            elif obj == "brand":
                data["record_type"] = "Brand"
                res = VehicleSpecService.create_spec(db, **data)
                if not res:
                    return {"intent": "CHAT", "text": "I encountered an error while creating the brand."}
                agent_output["text"] = f"Success! Created Brand {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj == "model":
                res = ModelService.create_model(db, **data)
                if not res:
                    return {"intent": "CHAT", "text": "I encountered an error while creating the model."}
                agent_output["text"] = f"Success! Created Model {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj == "product":
                from web.backend.app.services.product_service import ProductService
                res = ProductService.create_product(db, **data)
                if not res:
                    return {"intent": "CHAT", "text": "I encountered an error while creating the product."}
                agent_output["text"] = f"Success! Created Product {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj == "asset":
                from web.backend.app.services.asset_service import AssetService
                res = AssetService.create_asset(db, **data)
                if not res:
                    return {"intent": "CHAT", "text": "I encountered an error while creating the asset."}
                agent_output["text"] = f"Success! Registered Asset with VIN {res.vin} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, obj, str(res.id))
                return agent_output
            elif obj in ["message_template", "template"]:
                name = data.pop("name", "New Template")
                res = MessageTemplateService.create_template(db, name=name, **data)
                if not res:
                    return {"intent": "CHAT", "text": "I encountered an error while creating the message template."}
                agent_output["text"] = f"Success! Created Template: {res.name} (ID: {res.id})."
                ConversationContextStore.remember_created(conversation_id, "message_template", str(res.id))
                return agent_output

        if intent == "UPDATE" and record_id:
            if obj == "lead":
                data = cls._normalize_lead_lookup_inputs(db, data)
                res = LeadService.update_lead(db, record_id, **data)
                if res:
                    refreshed = LeadService.get_lead(db, record_id)
                    if refreshed:
                        return cls._build_lead_open_record_response(
                            db,
                            refreshed,
                            conversation_id,
                            action="update",
                            language_preference=agent_output.get("language_preference"),
                        )
                    agent_output["text"] = "I couldn't find that lead record."
                else:
                    agent_output["text"] = "I couldn't find that lead record."
                return agent_output
            elif obj == "contact":
                res = ContactService.update_contact(db, record_id, **data)
                if res:
                    refreshed = ContactService.get_contact(db, record_id)
                    if refreshed:
                        return cls._build_phase1_open_record_response(
                            db,
                            "contact",
                            refreshed,
                            conversation_id,
                            "update",
                            agent_output.get("language_preference"),
                        )
                    agent_output["text"] = f"Contact {record_id} not found."
                else:
                    agent_output["text"] = f"Contact {record_id} not found."
                return agent_output
            elif obj == "opportunity":
                res = OpportunityService.update_opportunity(db, record_id, **data)
                if res:
                    refreshed = OpportunityService.get_opportunity(db, record_id)
                    if refreshed:
                        return cls._build_phase1_open_record_response(
                            db,
                            "opportunity",
                            refreshed,
                            conversation_id,
                            "update",
                            agent_output.get("language_preference"),
                        )
                    agent_output["text"] = f"Opportunity {record_id} not found."
                else:
                    agent_output["text"] = f"Opportunity {record_id} not found."
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
