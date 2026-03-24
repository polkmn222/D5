import re
from typing import Dict, Any, Optional


class IntentPreClassifier:

    TYPO_MAP = {
        "laed": "lead",
        "leda": "lead",
        "contcat": "contact",
    }

    ACTION_CREATE = ["create", "add", "make", "만들", "생성", "등록", "추가"]
    ACTION_QUERY = ["show", "list", "all", "전체", "목록", "보여", "불러", "조회"]

    OBJECT_MAP = {
        "lead": "lead",
        "leads": "lead",
        "리드": "lead",
        "리드를": "lead",
        "contact": "contact",
        "contacts": "contact",
        "연락처": "contact",
        "연락처를": "contact",
        "opportunity": "opportunity",
        "opportunities": "opportunity",
        "기회": "opportunity",
        "기회를": "opportunity",
        "product": "product",
        "products": "product",
        "상품": "product",
        "상품을": "product",
        "asset": "asset",
        "assets": "asset",
        "자산": "asset",
        "자산을": "asset",
        "brand": "brand",
        "brands": "brand",
        "브랜드": "brand",
        "model": "model",
        "models": "model",
        "모델": "model",
        "template": "message_template",
        "templates": "message_template",
        "message template": "message_template",
        "message templates": "message_template",
    }

    CREATE_REQUIREMENTS = {
        "lead": "last name and status",
        "contact": "last name and status",
        "opportunity": "name, stage, and amount",
        "brand": "name",
        "model": "name and brand",
        "product": "name and base price",
        "asset": "VIN",
    }

    CREATE_FIELD_HINTS = {
        "lead": ["last name", "last_name", "status", "email", "phone"],
        "contact": ["last name", "last_name", "status", "email", "phone"],
        "opportunity": ["name", "stage", "amount", "probability"],
        "brand": ["name", "description"],
        "model": ["name", "brand", "description"],
        "product": ["name", "price", "base price", "base_price"],
        "asset": ["vin", "status", "plate"],
    }

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""
        t = text.lower().strip()
        for typo, correct in cls.TYPO_MAP.items():
            t = t.replace(typo, correct)
        return t

    @classmethod
    def _contains_action(cls, normalized: str, candidates: list[str]) -> bool:
        english_tokens = set(re.findall(r"[a-z]+", normalized))
        for word in candidates:
            if re.fullmatch(r"[a-z ]+", word):
                if word in english_tokens:
                    return True
            elif word in normalized:
                return True
        return False

    @classmethod
    def detect(cls, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None

        normalized = cls.normalize(text)

        # ---- Phase 50: Confidence Guardrails ----
        tokens = re.findall(r"\w+", normalized)

        # Too long → likely complex sentence → send to LLM
        if len(tokens) > 7:
            return None

        # Contains time/date/condition keywords → likely complex query
        complex_markers = [
            "today", "tomorrow", "yesterday", "this week", "last week",
            "이번", "저번", "내일", "어제", "조건", "where", "if",
            "just created", "recently created", "방금 생성", "방금 만든", "최근 생성", "최근 만든"
        ]
        if any(marker in normalized for marker in complex_markers):
            recent_object = None
            for key, value in cls.OBJECT_MAP.items():
                if key in normalized:
                    recent_object = value
                    break
            if recent_object and cls._contains_action(normalized, cls.ACTION_QUERY):
                return {
                    "intent": "QUERY",
                    "object_type": recent_object,
                    "sql": None,
                    "score": 0.99,
                }
            return None

        detected_object = None
        detected_key = None
        for key, value in cls.OBJECT_MAP.items():
            if key in normalized:
                detected_object = value
                detected_key = key
                break

        if not detected_object:
            return None

        is_create = cls._contains_action(normalized, cls.ACTION_CREATE)
        is_query = cls._contains_action(normalized, cls.ACTION_QUERY)

        recent_query_markers = [
            "just created", "recently created", "방금 생성", "방금 만든", "최근 생성", "최근 만든"
        ]
        if any(marker in normalized for marker in recent_query_markers):
            return {
                "intent": "QUERY",
                "object_type": detected_object,
                "sql": None,
                "score": 0.99,
            }

        if is_create:
            field_hints = cls.CREATE_FIELD_HINTS.get(detected_object, [])
            if any(hint in normalized for hint in field_hints) or ":" in text:
                return None
            required_fields = cls.CREATE_REQUIREMENTS.get(detected_object, "the required fields")
            return {
                "intent": "CHAT",
                "object_type": detected_object,
                "text": f"Sure. I can help create a {detected_object}. Please provide {required_fields}.",
                "score": 0.99,
            }

        if is_query or normalized.strip() == detected_key:
            return {
                "intent": "QUERY",
                "object_type": detected_object,
                "sql": None,
                "score": 0.99,
            }

        return None
