from typing import Any, Dict, Optional, cast


class ConversationContextStore:
    _store: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_context(cls, conversation_id: Optional[str]) -> Dict[str, Any]:
        if not conversation_id:
            return {}
        return cls._store.setdefault(conversation_id, {})

    @classmethod
    def remember_created(cls, conversation_id: Optional[str], object_type: str, record_id: Optional[str]) -> None:
        if not conversation_id or not object_type or not record_id:
            return
        context = cls._store.setdefault(conversation_id, {})
        context["last_created"] = {"object_type": object_type, "record_id": record_id}
        context["last_object"] = object_type
        context["last_record_id"] = record_id
        context["last_intent"] = "CREATE"

    @classmethod
    def remember_object(
        cls,
        conversation_id: Optional[str],
        object_type: Optional[str],
        intent: Optional[str],
        record_id: Optional[str] = None,
    ) -> None:
        if not conversation_id or not object_type:
            return
        context = cls._store.setdefault(conversation_id, {})
        context["last_object"] = object_type
        if intent:
            context["last_intent"] = intent
        if intent == "QUERY":
            context["last_query_object"] = object_type
        if record_id:
            context["last_record_id"] = record_id

    @classmethod
    def remember_pending_delete(
        cls,
        conversation_id: Optional[str],
        object_type: str,
        record_id: Optional[str] = None,
        ids: Optional[list[str]] = None,
        labels: Optional[list[str]] = None,
    ) -> None:
        if not conversation_id or not object_type or (not record_id and not ids):
            return
        context = cls._store.setdefault(conversation_id, {})
        payload = cast(Dict[str, Any], {"object_type": object_type})
        if record_id:
            payload["record_id"] = record_id
        if ids:
            payload["ids"] = list(ids)
        if labels:
            payload["labels"] = list(labels)
        context["pending_delete"] = payload

    @classmethod
    def get_pending_delete(cls, conversation_id: Optional[str]) -> Dict[str, Any]:
        if not conversation_id:
            return {}
        return cls._store.setdefault(conversation_id, {}).get("pending_delete") or {}

    @classmethod
    def clear_pending_delete(cls, conversation_id: Optional[str]) -> None:
        if not conversation_id:
            return
        context = cls._store.setdefault(conversation_id, {})
        context.pop("pending_delete", None)

    @classmethod
    def remember_selection(cls, conversation_id: Optional[str], selection: Optional[Dict[str, Any]]) -> None:
        if not conversation_id or not selection:
            return
        object_type = selection.get("object_type")
        ids = selection.get("ids") or []
        labels = selection.get("labels") or []
        context = cls._store.setdefault(conversation_id, {})
        context["selection"] = {"object_type": object_type, "ids": list(ids), "labels": list(labels)}

    @classmethod
    def remember_pending_create(cls, conversation_id: Optional[str], object_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        if not conversation_id or not object_type:
            return
        context = cls._store.setdefault(conversation_id, {})
        context["pending_create"] = {"object_type": object_type, "data": dict(data or {})}

    @classmethod
    def get_pending_create(cls, conversation_id: Optional[str]) -> Dict[str, Any]:
        if not conversation_id:
            return {}
        return cls._store.setdefault(conversation_id, {}).get("pending_create") or {}

    @classmethod
    def clear_pending_create(cls, conversation_id: Optional[str]) -> None:
        if not conversation_id:
            return
        context = cls._store.setdefault(conversation_id, {})
        context.pop("pending_create", None)

    @classmethod
    def get_selection(cls, conversation_id: Optional[str]) -> Dict[str, Any]:
        if not conversation_id:
            return {}
        return cls._store.setdefault(conversation_id, {}).get("selection") or {}

    @classmethod
    def clear(cls, conversation_id: Optional[str]) -> None:
        if conversation_id and conversation_id in cls._store:
            del cls._store[conversation_id]
