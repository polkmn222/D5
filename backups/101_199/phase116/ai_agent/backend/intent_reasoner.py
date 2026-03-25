import re
from typing import Any, Dict, List, Optional

from .intent_preclassifier import IntentPreClassifier


class IntentReasoner:
    ACTION_MAP = {
        "CREATE": ["create", "add", "make", "만들", "생성", "등록", "추가"],
        "QUERY": ["show", "list", "all", "전체", "목록", "보여"],
        "UPDATE": ["update", "edit", "change", "수정", "변경"],
        "DELETE": ["delete", "remove", "삭제"],
    }

    COMPLEX_MARKERS = [
        "today", "tomorrow", "yesterday", "this week", "last week",
        "이번", "저번", "내일", "어제", "조건", "where", "if",
        "just created", "recently created", "방금 생성", "방금 만든",
        "created this week", "생성된", "최근 생성", "최근 만든", "status",
    ]

    @classmethod
    def _detect_objects(cls, normalized: str) -> List[str]:
        english_tokens = set(re.findall(r"[a-z]+", normalized))
        objects: List[str] = []
        for key, value in IntentPreClassifier.OBJECT_MAP.items():
            matched = False
            if re.fullmatch(r"[a-z]+", key):
                matched = key in english_tokens
            else:
                matched = key in normalized
            if matched and value not in objects:
                objects.append(value)
        return objects

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
