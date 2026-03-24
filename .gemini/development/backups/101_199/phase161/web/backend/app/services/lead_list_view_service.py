import json
import logging

from sqlalchemy.orm import Session

from db.models import LeadListView
from web.backend.app.utils.sf_id import generate_sf_id
from web.backend.app.utils.timezone import get_kst_now_naive

logger = logging.getLogger(__name__)


class LeadListViewService:
    OWNER_KEY = "default"
    OBJECT_TYPE = "Lead"
    BUILTIN_VIEWS = (
        {"id": "all", "label": "All Leads", "source": "all"},
        {"id": "recent", "label": "Recently Viewed", "source": "recent"},
    )

    @classmethod
    def _resolve_context(cls, object_type: str | None = None, builtin_views: tuple[dict, ...] | None = None) -> tuple[str, tuple[dict, ...]]:
        resolved_object_type = object_type or cls.OBJECT_TYPE
        resolved_builtin_views = builtin_views or cls.BUILTIN_VIEWS
        return resolved_object_type, resolved_builtin_views

    @classmethod
    def _resolve_view_id(cls, view_id: str, builtin_views: tuple[dict, ...]) -> str:
        if view_id in {"all", "recent"}:
            matched = next((view["id"] for view in builtin_views if view.get("source") == view_id), None)
            if matched:
                return matched
        return view_id

    @classmethod
    def _normalize_columns(cls, visible_columns: list[str] | None, default_columns: list[str]) -> list[str]:
        if not visible_columns:
            return default_columns[:]
        ordered_columns = [column for column in default_columns if column in visible_columns]
        return ordered_columns or default_columns[:]

    @classmethod
    def _normalize_filters(cls, filters: dict | None) -> dict:
        filters = filters or {}
        conditions = []
        for condition in filters.get("conditions", []):
            if not isinstance(condition, dict):
                continue
            field = str(condition.get("field") or "").strip()
            operator = str(condition.get("operator") or "contains").strip()
            value = str(condition.get("value") or "").strip()
            if field and operator and value:
                conditions.append({"field": field, "operator": operator, "value": value})

        return {
            "searchTerm": str(filters.get("searchTerm") or "").strip(),
            "logic": "or" if str(filters.get("logic") or "and").lower() == "or" else "and",
            "conditions": conditions,
        }

    @classmethod
    def _serialize_view(cls, view: LeadListView, default_columns: list[str]) -> dict:
        try:
            visible_columns = json.loads(view.visible_columns_json or "[]")
        except json.JSONDecodeError:
            visible_columns = []

        try:
            filters = json.loads(view.filters_json or "{}")
        except json.JSONDecodeError:
            filters = {}

        return {
            "id": view.id,
            "label": view.label,
            "source": view.source,
            "visibleColumns": cls._normalize_columns(visible_columns, default_columns),
            "filters": cls._normalize_filters(filters),
            "editable": not view.is_system,
            "isPinned": bool(view.is_pinned),
        }

    @classmethod
    def ensure_builtin_views(
        cls,
        db: Session,
        default_columns: list[str],
        object_type: str | None = None,
        builtin_views: tuple[dict, ...] | None = None,
    ) -> None:
        resolved_object_type, resolved_builtin_views = cls._resolve_context(object_type, builtin_views)
        changed = False
        default_columns_json = json.dumps(default_columns)

        for builtin in resolved_builtin_views:
            record = (
                db.query(LeadListView)
                .filter(
                    LeadListView.id == builtin["id"],
                    LeadListView.owner_key == cls.OWNER_KEY,
                    LeadListView.object_type == resolved_object_type,
                )
                .first()
            )

            if not record:
                db.add(LeadListView(
                    id=builtin["id"],
                    owner_key=cls.OWNER_KEY,
                    object_type=resolved_object_type,
                    label=builtin["label"],
                    source=builtin["source"],
                    visible_columns_json=default_columns_json,
                    filters_json=json.dumps(cls._normalize_filters({})),
                    is_system=True,
                    is_pinned=False,
                    created_at=get_kst_now_naive(),
                    updated_at=get_kst_now_naive(),
                ))
                changed = True
                continue

            if record.label != builtin["label"]:
                record.label = builtin["label"]
                changed = True
            if record.source != builtin["source"]:
                record.source = builtin["source"]
                changed = True
            if record.visible_columns_json != default_columns_json:
                record.visible_columns_json = default_columns_json
                changed = True
            if not record.is_system:
                record.is_system = True
                changed = True

        if changed:
            db.commit()

    @classmethod
    def list_views(
        cls,
        db: Session,
        default_columns: list[str],
        object_type: str | None = None,
        builtin_views: tuple[dict, ...] | None = None,
    ) -> list[dict]:
        resolved_object_type, resolved_builtin_views = cls._resolve_context(object_type, builtin_views)
        cls.ensure_builtin_views(db, default_columns, resolved_object_type, resolved_builtin_views)
        records = (
            db.query(LeadListView)
            .filter(
                LeadListView.owner_key == cls.OWNER_KEY,
                LeadListView.object_type == resolved_object_type,
                LeadListView.deleted_at == None,
            )
            .order_by(LeadListView.is_system.desc(), LeadListView.created_at.asc())
            .all()
        )
        return [cls._serialize_view(record, default_columns) for record in records]

    @classmethod
    def get_pinned_view_id(
        cls,
        db: Session,
        default_columns: list[str],
        object_type: str | None = None,
        builtin_views: tuple[dict, ...] | None = None,
    ) -> str | None:
        resolved_object_type, resolved_builtin_views = cls._resolve_context(object_type, builtin_views)
        cls.ensure_builtin_views(db, default_columns, resolved_object_type, resolved_builtin_views)
        record = (
            db.query(LeadListView)
            .filter(
                LeadListView.owner_key == cls.OWNER_KEY,
                LeadListView.object_type == resolved_object_type,
                LeadListView.deleted_at == None,
                LeadListView.is_pinned == True,
            )
            .first()
        )
        return record.id if record else None

    @classmethod
    def create_view(
        cls,
        db: Session,
        payload: dict,
        default_columns: list[str],
        object_type: str | None = None,
        builtin_views: tuple[dict, ...] | None = None,
    ) -> dict:
        resolved_object_type, resolved_builtin_views = cls._resolve_context(object_type, builtin_views)
        cls.ensure_builtin_views(db, default_columns, resolved_object_type, resolved_builtin_views)
        label = str(payload.get("label") or "").strip()
        if not label:
            raise ValueError("View label is required")

        record = LeadListView(
            id=generate_sf_id("LVW"),
            owner_key=cls.OWNER_KEY,
            object_type=resolved_object_type,
            label=label,
            source="recent" if payload.get("source") == "recent" else "all",
            visible_columns_json=json.dumps(cls._normalize_columns(payload.get("visibleColumns"), default_columns)),
            filters_json=json.dumps(cls._normalize_filters(payload.get("filters"))),
            is_system=False,
            is_pinned=False,
            created_at=get_kst_now_naive(),
            updated_at=get_kst_now_naive(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return cls._serialize_view(record, default_columns)

    @classmethod
    def update_view(
        cls,
        db: Session,
        view_id: str,
        payload: dict,
        default_columns: list[str],
        object_type: str | None = None,
        builtin_views: tuple[dict, ...] | None = None,
    ) -> dict:
        resolved_object_type, resolved_builtin_views = cls._resolve_context(object_type, builtin_views)
        cls.ensure_builtin_views(db, default_columns, resolved_object_type, resolved_builtin_views)
        record = (
            db.query(LeadListView)
            .filter(
                LeadListView.id == view_id,
                LeadListView.owner_key == cls.OWNER_KEY,
                LeadListView.object_type == resolved_object_type,
                LeadListView.deleted_at == None,
            )
            .first()
        )
        if not record:
            raise ValueError("List view not found")
        if record.is_system:
            raise ValueError("Built-in views cannot be edited")

        label = str(payload.get("label") or record.label).strip()
        if not label:
            raise ValueError("View label is required")

        record.label = label
        record.source = "recent" if payload.get("source") == "recent" else "all"
        record.visible_columns_json = json.dumps(cls._normalize_columns(payload.get("visibleColumns"), default_columns))
        record.filters_json = json.dumps(cls._normalize_filters(payload.get("filters")))
        record.updated_at = get_kst_now_naive()
        db.commit()
        db.refresh(record)
        return cls._serialize_view(record, default_columns)

    @classmethod
    def delete_view(cls, db: Session, view_id: str, object_type: str | None = None, builtin_views: tuple[dict, ...] | None = None) -> None:
        resolved_object_type, resolved_builtin_views = cls._resolve_context(object_type, builtin_views)
        view_id = cls._resolve_view_id(view_id, resolved_builtin_views)
        record = (
            db.query(LeadListView)
            .filter(
                LeadListView.id == view_id,
                LeadListView.owner_key == cls.OWNER_KEY,
                LeadListView.object_type == resolved_object_type,
                LeadListView.deleted_at == None,
            )
            .first()
        )
        if not record:
            raise ValueError("List view not found")
        if record.is_system:
            raise ValueError("Built-in views cannot be deleted")

        record.deleted_at = get_kst_now_naive()
        record.is_pinned = False
        record.updated_at = get_kst_now_naive()
        db.commit()

    @classmethod
    def set_pinned_view(
        cls,
        db: Session,
        view_id: str,
        default_columns: list[str],
        pinned: bool = True,
        object_type: str | None = None,
        builtin_views: tuple[dict, ...] | None = None,
    ) -> str | None:
        resolved_object_type, resolved_builtin_views = cls._resolve_context(object_type, builtin_views)
        view_id = cls._resolve_view_id(view_id, resolved_builtin_views)
        cls.ensure_builtin_views(db, default_columns, resolved_object_type, resolved_builtin_views)
        records = (
            db.query(LeadListView)
            .filter(
                LeadListView.owner_key == cls.OWNER_KEY,
                LeadListView.object_type == resolved_object_type,
                LeadListView.deleted_at == None,
            )
            .all()
        )

        target = next((record for record in records if record.id == view_id), None)
        if not target:
            raise ValueError("List view not found")

        for record in records:
            record.is_pinned = False
            record.updated_at = get_kst_now_naive()

        if pinned:
            target.is_pinned = True
            target.updated_at = get_kst_now_naive()

        db.commit()
        return target.id if pinned else None
