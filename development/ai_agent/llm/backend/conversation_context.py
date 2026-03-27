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
    def remember_query_results(
        cls,
        conversation_id: Optional[str],
        object_type: Optional[str],
        results: Optional[list[Dict[str, Any]]],
    ) -> None:
        if not conversation_id or not object_type:
            return
        context = cls._store.setdefault(conversation_id, {})
        ranked_results = []
        for row in list(results or [])[:10]:
            record_id = row.get("id")
            if not record_id:
                continue
            label = (
                row.get("display_name")
                or row.get("name")
                or row.get("contact_display_name")
                or row.get("phone")
                or str(record_id)
            )
            ranked_results.append(
                {
                    "record_id": str(record_id),
                    "label": str(label),
                }
            )
        context["last_query_object"] = object_type
        context["last_query_results"] = ranked_results

    @classmethod
    def get_query_results(cls, conversation_id: Optional[str]) -> Dict[str, Any]:
        if not conversation_id:
            return {}
        context = cls._store.setdefault(conversation_id, {})
        return {
            "object_type": context.get("last_query_object"),
            "results": list(context.get("last_query_results") or []),
        }

    @classmethod
    def build_reasoning_context(
        cls,
        conversation_id: Optional[str],
        selection: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        context = cls.get_context(conversation_id)
        selection_payload = selection or context.get("selection") or {}
        selection_ids = list(selection_payload.get("ids") or [])
        selection_labels = list(selection_payload.get("labels") or [])
        query_results = list((context.get("last_query_results") or [])[:5])
        last_created = dict(context.get("last_created") or {})
        last_record = {
            "object_type": context.get("last_object"),
            "record_id": context.get("last_record_id"),
        }
        selection_object_type = selection_payload.get("object_type")
        query_object_type = context.get("last_query_object")
        has_selection_conflict = bool(
            last_record.get("object_type")
            and selection_object_type
            and selection_ids
            and (
                last_record.get("object_type") != selection_object_type
                or (
                    len(selection_ids) == 1
                    and last_record.get("record_id")
                    and last_record.get("record_id") != selection_ids[0]
                )
            )
        )
        return {
            "conversation_id": conversation_id,
            "last_intent": context.get("last_intent"),
            "last_created": last_created,
            "last_record": last_record,
            "selection": {
                "object_type": selection_object_type,
                "record_ids": selection_ids,
                "labels": selection_labels,
                "count": len(selection_ids),
            },
            "query_results": {
                "object_type": query_object_type,
                "results": query_results,
                "count": len(query_results),
            },
            "safety": {
                "has_selection_conflict": has_selection_conflict,
                "has_multi_selection": len(selection_ids) > 1,
                "has_query_results": bool(query_results),
                "query_result_count": len(query_results),
                "last_created_matches_last_record": bool(
                    last_created.get("object_type") == last_record.get("object_type")
                    and last_created.get("record_id")
                    and last_created.get("record_id") == last_record.get("record_id")
                ),
            },
        }

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
