import re
from typing import Dict, Any, Optional


class IntentPreClassifier:

    TYPO_MAP = {
        "laed": "lead",
        "leda": "lead",
        "contcat": "contact",
    }

    ACTION_CREATE = ["create", "add", "make", "만들", "생성", "등록", "추가"]
    ACTION_QUERY = ["show", "list", "all", "전체", "목록", "보여"]

    OBJECT_MAP = {
        "lead": "lead",
        "리드": "lead",
        "contact": "contact",
        "연락처": "contact",
        "opportunity": "opportunity",
        "기회": "opportunity",
        "product": "product",
        "상품": "product",
        "asset": "asset",
        "자산": "asset",
        "brand": "brand",
        "브랜드": "brand",
        "model": "model",
        "모델": "model",
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
            "이번", "저번", "내일", "어제", "조건", "where", "if"
        ]
        if any(marker in normalized for marker in complex_markers):
            return None

        detected_object = None
        for key, value in cls.OBJECT_MAP.items():
            if key in normalized:
                detected_object = value
                break

        if not detected_object:
            return None

        is_create = any(word in normalized for word in cls.ACTION_CREATE)
        is_query = any(word in normalized for word in cls.ACTION_QUERY)

        if is_create:
            return {
                "intent": "CREATE",
                "object_type": detected_object,
                "text": f"Sure. Please provide required fields to create {detected_object}.",
                "score": 0.99,
            }

        if is_query or normalized.strip() == detected_object:
            return {
                "intent": "QUERY",
                "object_type": detected_object,
                "sql": None,
                "score": 0.99,
            }

        return None
