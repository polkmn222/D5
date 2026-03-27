import json
import re
from typing import Any, Dict, List, Optional

from .intent_preclassifier import IntentPreClassifier


class IntentReasoner:
    LOW_CONFIDENCE = 0.4
    MIN_EXECUTION_CONFIDENCE = 0.6
    HIGH_CONFIDENCE = 0.85
    INTENT_TO_ACTION = {
        "QUERY": "query",
        "CREATE": "create",
        "UPDATE": "update",
        "DELETE": "delete",
        "MANAGE": "manage",
        "CHAT": "chat",
        "RECOMMEND": "recommend",
        "MODIFY_UI": "modify_ui",
        "SEND_MESSAGE": "send_message",
        "USAGE": "usage",
    }
    ACTION_TO_INTENT = {value: key for key, value in INTENT_TO_ACTION.items()}
    EXECUTABLE_INTENTS = {"QUERY", "CREATE", "UPDATE", "DELETE", "MANAGE"}
    ACTION_MAP = {
        "CREATE": ["create", "add", "make", "만들", "생성", "등록", "추가"],
        "QUERY": ["show", "list", "all", "전체", "목록", "보여"],
        "UPDATE": ["update", "edit", "change", "수정", "변경"],
        "DELETE": ["delete", "remove", "삭제"],
    }
    ALLOWED_INTENTS = {
        "QUERY",
        "CREATE",
        "UPDATE",
        "DELETE",
        "MANAGE",
        "CHAT",
        "RECOMMEND",
        "MODIFY_UI",
        "SEND_MESSAGE",
        "USAGE",
    }
    CONTEXT_REFERENCE_ALIASES = {
        "just_created": "last_created",
        "the_one_i_just_created": "last_created",
        "recently_created": "last_created",
        "i_just_added": "last_created",
        "just_added": "last_created",
        "from_before": "last_record",
        "we_were_just_looking_at": "last_record",
        "we_were_looking_at": "last_record",
        "last_created": "last_created",
        "the_last_one": "last_record",
        "last_one": "last_record",
        "that_one": "last_record",
        "that_record": "last_record",
        "selected": "selection",
        "selected_record": "selection",
        "selected_one": "selection",
        "recent_query_result": "query_result",
        "last_query_result": "query_result",
        "from_the_list": "query_result",
        "from_list": "query_result",
    }
    COMPLEX_MARKERS = [
        "today",
        "tomorrow",
        "yesterday",
        "this week",
        "last week",
        "이번",
        "저번",
        "내일",
        "어제",
        "조건",
        "where",
        "if",
        "just created",
        "recently created",
        "방금 생성",
        "방금 만든",
        "created this week",
        "생성된",
        "최근 생성",
        "최근 만든",
        "status",
    ]
    COMMON_FIELD_ALIASES = {
        "firstname": "first_name",
        "first_name": "first_name",
        "first name": "first_name",
        "fname": "first_name",
        "lastname": "last_name",
        "last_name": "last_name",
        "last name": "last_name",
        "surname": "last_name",
        "lname": "last_name",
        "email": "email",
        "phone": "phone",
        "mobile": "phone",
        "phone num": "phone",
        "phone number": "phone",
        "num": "phone",
        "status": "status",
        "stage": "stage",
        "amount": "amount",
        "probability": "probability",
        "name": "name",
    }
    NOISY_PHRASE_NORMALIZATIONS = {
        "can u": "can you",
        "pls ": "please ",
        "pls,": "please,",
        "opp ": "opportunity ",
        " opp": " opportunity",
        "phone num": "phone number",
        "i just added": "just added",
        "from before": "last record",
        "we were just looking at": "last record",
        "from the list": "query result",
    }

    @classmethod
    def _detect_objects(cls, normalized: str) -> List[str]:
        return IntentPreClassifier.detect_object_mentions(normalized)

    @classmethod
    def _detect_actions(cls, normalized: str) -> List[str]:
        english_tokens = set(re.findall(r"[a-z]+", normalized))
        actions: List[str] = []
        for action, keywords in cls.ACTION_MAP.items():
            for keyword in keywords:
                if re.fullmatch(r"[a-z]+", keyword):
                    matched = keyword in english_tokens
                else:
                    matched = keyword in normalized
                if matched:
                    actions.append(action)
                    break
        return actions

    @classmethod
    def clarify_if_needed(cls, text: str) -> Optional[Dict[str, Any]]:
        normalized = IntentPreClassifier.normalize(text)
        if any(marker in normalized for marker in cls.COMPLEX_MARKERS):
            return None

        objects = cls._detect_objects(normalized)
        actions = cls._detect_actions(normalized)

        if len(objects) > 1:
            object_names = ", ".join(objects)
            return {
                "intent": "CHAT",
                "text": f"I found multiple objects in your request ({object_names}). Which one would you like to work with?",
                "score": 1.0,
            }

        if len(actions) > 1:
            action_names = ", ".join(actions)
            return {
                "intent": "CHAT",
                "text": f"I found multiple actions in your request ({action_names}). Please clarify which action you want first.",
                "score": 1.0,
            }

        return None

    @classmethod
    def build_reasoning_prompt(
        cls,
        metadata: str,
        language_preference: Optional[str],
        reasoning_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        context_json = json.dumps(reasoning_context or {}, ensure_ascii=False, indent=2)
        return f"""
You are the "AI Agent" reasoning engine for an Automotive CRM (D4).

Your job is to interpret only ambiguous, contextual, or non-obvious requests after deterministic routing has already failed.
Do not override clear deterministic CRUD behavior.

DATABASE SCHEMA:
{metadata}

UI language preference: {language_preference or 'auto'}.
If UI language preference is `eng`, answer in English.
If UI language preference is `kor`, answer in Korean.

AVAILABLE CONTEXT:
{context_json}

RULES:
- Prefer safe clarification over guessing.
- Do not invent record IDs, field names, SQL columns, or object support.
- Supported object types in this fallback are: lead, contact, opportunity, brand, model, product, asset, message_template, message_send.
- `intent` is the validator-facing decision. `action` must match `intent` and must never contradict it.
- Use exactly one `object_type` when the request is executable. If the object is unclear or mixed, prefer clarification.
- For context references like "that one", "the last one", "from before", or "the one I just created", use `context_reference`.
- For phrases like "from the list" or "selected contact", use `query_result` or `selection` only when the provided context supports one safe record.
- Use `resolved_reference` only when the provided context supports one specific record safely.
- For create or update interpretation, use `fields_to_update` with normalized CRM field names only.
- For search/query interpretation, use `filters` for semantic filters. Use `sql` only when a real SQL query is necessary.
- If the wording sounds like a search but the filters are incomplete or weak, prefer clarification over guessing or switching to `MANAGE`.
- `MANAGE`, `UPDATE`, and `DELETE` require one validated target record. If the target is unclear, prefer clarification.
- If confidence is not high enough for a safe executable action, prefer clarification.
- If the user wording is noisy, casual, shorthand, or incomplete, keep the output conservative and do not guess beyond the available context.
- If the request is ambiguous, mixed-object, under-specified, or unsafe, set `requires_clarification` to true and ask one narrow question.

MINIMAL EXAMPLES:
User: "delete that one"
Safe JSON:
{{
  "intent": "CHAT",
  "action": "chat",
  "object_type": "lead",
  "filters": {{}},
  "fields_to_update": {{}},
  "context_reference": {{"kind": "that_one"}},
  "resolved_reference": {{}},
  "requires_clarification": true,
  "clarification_question": "Which specific lead do you want me to delete?",
  "confidence": 0.35,
  "text": "",
  "sql": ""
}}

User: "can u pull the contact i just added"
Safe JSON:
{{
  "intent": "MANAGE",
  "action": "manage",
  "object_type": "contact",
  "filters": {{}},
  "fields_to_update": {{}},
  "context_reference": {{"kind": "last_created", "object_type": "contact"}},
  "resolved_reference": {{}},
  "requires_clarification": false,
  "clarification_question": "",
  "confidence": 0.86,
  "text": "",
  "sql": ""
}}

User: "open the last contact from the list"
Safe JSON:
{{
  "intent": "MANAGE",
  "action": "manage",
  "object_type": "contact",
  "filters": {{}},
  "fields_to_update": {{}},
  "context_reference": {{"kind": "query_result", "index": -1, "object_type": "contact"}},
  "resolved_reference": {{}},
  "requires_clarification": false,
  "clarification_question": "",
  "confidence": 0.84,
  "text": "",
  "sql": ""
}}

STRICT JSON SHAPE:
{{
  "intent": "QUERY|CREATE|UPDATE|DELETE|MANAGE|CHAT|RECOMMEND|MODIFY_UI|SEND_MESSAGE|USAGE",
  "action": "query|create|update|delete|manage|chat|recommend|modify_ui|send_message|usage",
  "object_type": "lead|contact|opportunity|brand|model|product|asset|message_template|message_send",
  "filters": {{}},
  "fields_to_update": {{}},
  "context_reference": {{
    "kind": "last_created|last_record|selection|query_result",
    "index": 0,
    "object_type": "optional object type"
  }},
  "resolved_reference": {{
    "object_type": "lead",
    "record_id": "abc123"
  }},
  "requires_clarification": false,
  "clarification_question": "",
  "confidence": 0.0,
  "text": "",
  "sql": ""
}}
""".strip()

    @classmethod
    def _normalize_object_type(cls, value: Any) -> Optional[str]:
        return IntentPreClassifier.normalize_object_type(value)

    @classmethod
    def _normalize_intent(cls, value: Any, action: Any = None) -> str:
        raw = str(value or action or "CHAT").strip().upper().replace(" ", "_")
        if raw not in cls.ALLOWED_INTENTS:
            return "CHAT"
        return raw

    @classmethod
    def _normalize_action(cls, value: Any) -> Optional[str]:
        if not value:
            return None
        normalized = str(value).strip().lower().replace(" ", "_")
        if normalized in cls.ACTION_TO_INTENT:
            return normalized
        normalized_upper = normalized.upper()
        if normalized_upper in cls.INTENT_TO_ACTION:
            return cls.INTENT_TO_ACTION[normalized_upper]
        return None

    @classmethod
    def _resolve_intent_and_action(
        cls,
        raw_intent: Any,
        raw_action: Any,
    ) -> Dict[str, Any]:
        intent = cls._normalize_intent(raw_intent)
        action = cls._normalize_action(raw_action) or cls.INTENT_TO_ACTION.get(intent)
        expected_action = cls.INTENT_TO_ACTION.get(intent)
        if raw_action and expected_action and action and action != expected_action:
            return {
                "intent": "CHAT",
                "action": "chat",
                "conflict": True,
                "message": (
                    f"The fallback reasoning returned intent `{intent}` but action `{action}`. "
                    "Please restate the request so I can choose one safe action."
                ),
            }
        return {
            "intent": intent,
            "action": action or cls.INTENT_TO_ACTION.get(intent, "chat"),
            "conflict": False,
            "message": "",
        }

    @classmethod
    def _to_bool(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "y"}
        return bool(value)

    @classmethod
    def _to_confidence(cls, value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, score))

    @classmethod
    def _confidence_band(cls, confidence: float) -> str:
        if confidence < cls.LOW_CONFIDENCE:
            return "low"
        if confidence < cls.HIGH_CONFIDENCE:
            return "medium"
        return "high"

    @classmethod
    def _should_clarify_for_confidence(cls, intent: str, confidence: float) -> bool:
        if intent not in cls.EXECUTABLE_INTENTS:
            return False
        return confidence < cls.MIN_EXECUTION_CONFIDENCE

    @classmethod
    def _normalize_reference_kind(cls, kind: Any) -> Optional[str]:
        if not kind:
            return None
        normalized = str(kind).strip().lower().replace(" ", "_")
        return cls.CONTEXT_REFERENCE_ALIASES.get(normalized, normalized)

    @classmethod
    def _normalize_user_query(cls, user_query: str) -> str:
        normalized = IntentPreClassifier.normalize(user_query)
        for source, replacement in cls.NOISY_PHRASE_NORMALIZATIONS.items():
            normalized = normalized.replace(source, replacement)
        return normalized

    @classmethod
    def _normalize_reference(
        cls,
        reference: Any,
        default_object_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not isinstance(reference, dict):
            reference = {"kind": reference} if reference else {}
        index = reference.get("index")
        try:
            safe_index = int(index) if index is not None else 0
        except (TypeError, ValueError):
            safe_index = 0
        return {
            "kind": cls._normalize_reference_kind(reference.get("kind")),
            "index": safe_index,
            "object_type": cls._normalize_object_type(reference.get("object_type") or default_object_type),
        }

    @classmethod
    def _normalize_key(cls, key: Any) -> Optional[str]:
        if not key:
            return None
        normalized = str(key).strip().lower().replace("-", "_")
        normalized = re.sub(r"\s+", " ", normalized)
        alias = cls.COMMON_FIELD_ALIASES.get(normalized)
        if alias:
            return alias
        normalized = normalized.replace(" ", "_")
        if re.fullmatch(r"[a-z_]+", normalized):
            return normalized
        return None

    @classmethod
    def _normalize_dict_payload(cls, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            return {}
        normalized: Dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = cls._normalize_key(raw_key)
            if not key:
                continue
            if raw_value in ("", None, "null", "None"):
                continue
            normalized[key] = raw_value
        return normalized

    @classmethod
    def _build_chat_response(
        cls,
        text: str,
        object_type: Optional[str],
        confidence: float,
        context_reference: Optional[Dict[str, Any]] = None,
        resolved_reference: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        band = cls._confidence_band(confidence)
        return {
            "intent": "CHAT",
            "object_type": object_type,
            "text": text,
            "score": max(confidence, 0.5),
            "reasoning": {
                "context_reference": context_reference or {},
                "resolved_reference": resolved_reference or {},
                "confidence": confidence,
                "confidence_band": band,
            },
        }

    @classmethod
    def _contract_failure(
        cls,
        text: str,
        object_type: Optional[str],
        confidence: float,
        context_reference: Optional[Dict[str, Any]] = None,
        resolved_reference: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return cls._build_chat_response(
            text,
            object_type,
            confidence,
            context_reference,
            resolved_reference,
        )

    @classmethod
    def _object_label(cls, object_type: Optional[str]) -> str:
        return object_type or "record"

    @classmethod
    def _action_label(cls, intent: str) -> str:
        labels = {
            "MANAGE": "open or manage",
            "UPDATE": "update",
            "DELETE": "delete",
            "QUERY": "search for",
            "CREATE": "create",
        }
        return labels.get(intent, "work with")

    @classmethod
    def _field_summary(cls, data: Dict[str, Any]) -> str:
        if not data:
            return ""
        labels = [str(key).replace("_", " ") for key in data.keys()]
        if len(labels) == 1:
            return labels[0]
        if len(labels) == 2:
            return f"{labels[0]} and {labels[1]}"
        return ", ".join(labels[:-1]) + f", and {labels[-1]}"

    @classmethod
    def _resolve_context_reference(
        cls,
        context_reference: Dict[str, Any],
        reasoning_context: Optional[Dict[str, Any]],
        object_type: Optional[str],
    ) -> Dict[str, Any]:
        if not context_reference:
            return {}
        context = reasoning_context or {}
        desired_object_type = context_reference.get("object_type") or object_type
        kind = context_reference.get("kind")
        if kind == "last_created":
            candidate = dict(context.get("last_created") or {})
            candidate_object_type = cls._normalize_object_type(candidate.get("object_type"))
            if candidate.get("record_id") and (not desired_object_type or desired_object_type == candidate_object_type):
                return {"object_type": candidate_object_type, "record_id": candidate.get("record_id")}
            return {}
        if kind == "last_record":
            candidate = dict(context.get("last_record") or {})
            candidate_object_type = cls._normalize_object_type(candidate.get("object_type"))
            if candidate.get("record_id") and (not desired_object_type or desired_object_type == candidate_object_type):
                return {"object_type": candidate_object_type, "record_id": candidate.get("record_id")}
            return {}
        if kind == "selection":
            selection = dict(context.get("selection") or {})
            selection_ids = list(selection.get("record_ids") or [])
            selection_object_type = cls._normalize_object_type(selection.get("object_type"))
            if len(selection_ids) == 1 and (not desired_object_type or desired_object_type == selection_object_type):
                return {"object_type": selection_object_type, "record_id": selection_ids[0]}
            return {}
        if kind == "query_result":
            query_results = dict(context.get("query_results") or {})
            results = list(query_results.get("results") or [])
            index = context_reference.get("index") or 0
            query_object_type = cls._normalize_object_type(query_results.get("object_type"))
            if isinstance(index, int) and index < 0:
                index = len(results) + index
            if 0 <= index < len(results) and (not desired_object_type or desired_object_type == query_object_type):
                return {"object_type": query_object_type, "record_id": results[index].get("record_id")}
            return {}
        return {}

    @classmethod
    def _normalize_resolved_reference(
        cls,
        resolved_reference: Any,
        reasoning_context: Optional[Dict[str, Any]],
        object_type: Optional[str],
        context_reference: Dict[str, Any],
    ) -> Dict[str, Any]:
        resolved = resolved_reference if isinstance(resolved_reference, dict) else {}
        normalized = {
            "object_type": cls._normalize_object_type(resolved.get("object_type") or object_type),
            "record_id": resolved.get("record_id"),
        }
        if normalized["record_id"]:
            return normalized
        return cls._resolve_context_reference(context_reference, reasoning_context, object_type)

    @classmethod
    def validate_reasoning_output(
        cls,
        raw_output: Any,
        user_query: str,
        reasoning_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not isinstance(raw_output, dict):
            return cls._build_chat_response(
                "I need a little more detail before I can safely help with that request.",
                None,
                0.0,
            )

        confidence = cls._to_confidence(raw_output.get("confidence", raw_output.get("score")))
        confidence_band = cls._confidence_band(confidence)
        intent_resolution = cls._resolve_intent_and_action(
            raw_output.get("intent"),
            raw_output.get("action"),
        )
        intent = intent_resolution["intent"]
        action = intent_resolution["action"]
        normalized_query = cls._normalize_user_query(user_query)
        explicit_objects = IntentPreClassifier.detect_object_mentions(normalized_query)
        object_type = cls._normalize_object_type(raw_output.get("object_type"))
        if not object_type and len(explicit_objects) == 1:
            object_type = explicit_objects[0]
        text = str(raw_output.get("text") or "").strip()
        filters = cls._normalize_dict_payload(raw_output.get("filters"))
        data = cls._normalize_dict_payload(raw_output.get("fields_to_update"))
        if not data and isinstance(raw_output.get("data"), dict):
            data = cls._normalize_dict_payload(raw_output.get("data"))
        context_reference = cls._normalize_reference(raw_output.get("context_reference"), object_type)
        resolved_reference = cls._normalize_resolved_reference(
            raw_output.get("resolved_reference"),
            reasoning_context,
            object_type,
            context_reference,
        )
        if resolved_reference.get("object_type") and not object_type:
            object_type = resolved_reference["object_type"]
        sql = raw_output.get("sql") if isinstance(raw_output.get("sql"), str) and raw_output.get("sql").strip() else None
        clarification_question = str(raw_output.get("clarification_question") or "").strip()
        requires_clarification = cls._to_bool(raw_output.get("requires_clarification"))

        if intent_resolution["conflict"]:
            return cls._contract_failure(
                intent_resolution["message"],
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if len(explicit_objects) > 1:
            return cls._contract_failure(
                (
                    f"I found multiple objects in your request ({', '.join(explicit_objects)}). "
                    "Please tell me which single object you want me to work with first."
                ),
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if explicit_objects and object_type and object_type not in explicit_objects:
            return cls._contract_failure(
                (
                    f"Your request mentions {', '.join(explicit_objects)}, but the fallback reasoning resolved {object_type}. "
                    "Please name the one object you want so I do not act on the wrong record."
                ),
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if (
            resolved_reference.get("object_type")
            and object_type
            and resolved_reference["object_type"] != object_type
        ):
            return cls._contract_failure(
                (
                    f"I found a {resolved_reference['object_type']} record in context, but your request is targeting {object_type}. "
                    f"Please tell me whether you want the {resolved_reference['object_type']} record from context or a specific {object_type} record."
                ),
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if requires_clarification:
            return cls._contract_failure(
                clarification_question or text or "Please clarify the request before I act on it.",
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if intent == "CHAT":
            return {
                "intent": "CHAT",
                "object_type": object_type,
                "text": text or clarification_question or "Please tell me what you want me to do.",
                "score": confidence,
                "reasoning": {
                    "filters": filters,
                    "fields_to_update": data,
                    "context_reference": context_reference,
                    "resolved_reference": resolved_reference,
                    "confidence": confidence,
                    "confidence_band": confidence_band,
                    "action": action,
                    "user_query": user_query,
                },
            }

        if intent in cls.EXECUTABLE_INTENTS and not object_type:
            if context_reference.get("kind"):
                if context_reference["kind"] == "query_result":
                    return cls._contract_failure(
                        "I can tell you are referring to something from the current list, but I still need the object and the exact item from that list before I act. Please name the object and which result you mean.",
                        None,
                        confidence,
                        context_reference,
                        resolved_reference,
                    )
                return cls._contract_failure(
                    "I can tell you are referring to an earlier record in context, but I still need the object and the exact record before I act. Please name the object and the specific record you mean.",
                    None,
                    confidence,
                    context_reference,
                    resolved_reference,
                )
            return cls._contract_failure(
                f"The fallback reasoning did not identify an object for this {action} request. Please name the object you want me to work with.",
                None,
                confidence,
                context_reference,
                resolved_reference,
            )

        if intent == "QUERY" and not (filters or sql or resolved_reference.get("record_id") or context_reference.get("kind")):
            target_name = cls._object_label(object_type)
            return cls._contract_failure(
                (
                    f"I can tell this sounds like a {target_name} search, but I do not have enough detail to run it safely yet. "
                    f"Please add one filter, date range, or a specific record reference."
                ),
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if intent == "QUERY" and data:
            return cls._contract_failure(
                "The fallback reasoning mixed query filters with update fields. Please restate the request as either a search or an edit.",
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if intent in {"CREATE", "UPDATE"} and sql:
            return cls._contract_failure(
                f"The fallback reasoning returned SQL for a {action} request, which is not executable safely. Please restate the request as a clear {action}.",
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if intent == "CREATE" and not data:
            return cls._contract_failure(
                f"The fallback reasoning did not produce any fields to create the {cls._object_label(object_type)}. Please provide the fields you want to set.",
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if intent == "UPDATE" and not data:
            return cls._contract_failure(
                f"The fallback reasoning did not produce any fields to update on the {cls._object_label(object_type)}. Please tell me what you want to change.",
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if cls._should_clarify_for_confidence(intent, confidence):
            target_name = cls._object_label(object_type)
            return cls._contract_failure(
                clarification_question or (
                    f"I only have {confidence_band} confidence in this {target_name} request, so I am not safe to {cls._action_label(intent)} it yet. "
                    f"Please restate the {target_name} and the action in one sentence."
                ),
                object_type,
                confidence,
                context_reference,
                resolved_reference,
            )

        if intent in {"MANAGE", "UPDATE", "DELETE"}:
            if not resolved_reference.get("record_id"):
                target_name = cls._object_label(object_type)
                safety = dict((reasoning_context or {}).get("safety") or {})
                if safety.get("has_multi_selection"):
                    message = (
                        f"I found multiple selected {target_name} records, so I cannot pick one safely. "
                        f"Please name the exact {target_name} or select only one record first."
                    )
                elif safety.get("has_selection_conflict"):
                    message = (
                        "I found more than one possible record in context, so I cannot choose safely. "
                        f"Please name the exact {target_name} you want."
                    )
                elif context_reference.get("kind") == "query_result":
                    message = (
                        f"I can tell you mean something from the current {target_name} list, but I cannot safely pick the exact result yet. "
                        f"Please name the {target_name} or say which result from the list you want."
                    )
                elif context_reference.get("kind") in {"last_record", "last_created"}:
                    message = (
                        f"I can tell you mean a recent {target_name}, but I still need the exact {target_name} record before I can {cls._action_label(intent)} it safely. "
                        f"Please give the {target_name} name, ID, or one clear selection."
                    )
                else:
                    message = (
                        f"I need a specific {target_name} record before I can {cls._action_label(intent)} it. "
                        f"Please give the {target_name} name, ID, or a single clear selection."
                    )
                if intent == "UPDATE" and data:
                    field_summary = cls._field_summary(data)
                    if field_summary:
                        message += f" I can keep the requested change to {field_summary} once you identify the record."
                return cls._contract_failure(
                    clarification_question or message,
                    object_type,
                    confidence,
                    context_reference,
                    {},
                )

        if intent in {"CREATE", "UPDATE"} and not isinstance(data, dict):
            data = {}

        payload: Dict[str, Any] = {
            "intent": intent,
            "object_type": object_type,
            "text": text,
            "score": confidence,
            "reasoning": {
                "filters": filters,
                "fields_to_update": data,
                "context_reference": context_reference,
                "resolved_reference": resolved_reference,
                "confidence": confidence,
                "confidence_band": confidence_band,
                "action": action,
                "user_query": user_query,
            },
        }

        if resolved_reference.get("record_id"):
            payload["record_id"] = resolved_reference["record_id"]

        if intent == "QUERY":
            if filters:
                payload["data"] = dict(filters)
            if sql:
                payload["sql"] = sql
        elif intent in {"CREATE", "UPDATE"}:
            payload["data"] = dict(data)
        elif sql and intent not in {"CHAT", "MANAGE"}:
            payload["sql"] = sql

        if not payload.get("text") and intent == "CHAT":
            payload["text"] = clarification_question or "I need a little more detail before I can safely help with that request."

        return payload
