from sqlalchemy import DateTime, select
from sqlalchemy.orm import Session
from typing import List, Optional, Type, TypeVar, Generic
import logging
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.timezone import get_kst_now_naive

logger = logging.getLogger(__name__)

T = TypeVar("T")

class BaseService(Generic[T]):
    model: Type[T]
    object_name: str

    @classmethod
    def _normalize_kwargs(cls, db: Session, kwargs: dict) -> tuple[dict, set[str]]:
        normalized = {}
        force_null_fields = set(kwargs.pop("_force_null_fields", []) or [])
        table_columns = cls.model.__table__.columns

        for key, value in kwargs.items():
            column = table_columns.get(key)
            if isinstance(value, str):
                value = value.strip()
            if column is not None and value == "":
                if column.foreign_keys or isinstance(column.type, DateTime):
                    value = None
                    force_null_fields.add(key)
            if column is not None and column.foreign_keys and value is not None:
                cls._validate_foreign_key(db, column, value)
            normalized[key] = value

        return normalized, force_null_fields

    @staticmethod
    def _validate_foreign_key(db: Session, column, value) -> None:
        foreign_key = next(iter(column.foreign_keys), None)
        if foreign_key is None:
            return
        target_column = foreign_key.column
        stmt = select(target_column).where(target_column == value)
        if "deleted_at" in target_column.table.c:
            stmt = stmt.where(target_column.table.c.deleted_at.is_(None))
        existing = db.execute(stmt).scalar_one_or_none()
        if existing is None:
            raise ValueError(f"Invalid lookup value for {column.name}: {value}")

    @classmethod
    def create(cls, db: Session, **kwargs) -> T:
        try:
            obj_id = get_id(cls.object_name)
            kwargs, _ = cls._normalize_kwargs(db, kwargs)
            if hasattr(cls.model, "created_by") and kwargs.get("created_by") is None:
                kwargs["created_by"] = "System"
            if hasattr(cls.model, "updated_by") and kwargs.get("updated_by") is None:
                kwargs["updated_by"] = kwargs.get("created_by") or "System"
            db_obj = cls.model(id=obj_id, **kwargs)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            logger.info(f"Created {cls.model.__name__}: {obj_id}")
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating {cls.model.__name__}: {e}")
            raise e

    @classmethod
    def get(cls, db: Session, obj_id: str) -> Optional[T]:
        try:
            return db.query(cls.model).filter(cls.model.id == obj_id, cls.model.deleted_at == None).first()
        except Exception as e:
            logger.error(f"Error getting {cls.model.__name__} {obj_id}: {e}")
            return None

    @classmethod
    def list(cls, db: Session, **filters) -> List[T]:
        try:
            query = db.query(cls.model).filter(cls.model.deleted_at == None)
            for attr, value in filters.items():
                if hasattr(cls.model, attr) and value is not None:
                    query = query.filter(getattr(cls.model, attr) == value)
            return query.all()
        except Exception as e:
            logger.error(f"Error listing {cls.model.__name__}: {e}")
            return []

    @classmethod
    def update(cls, db: Session, obj_id: str, **kwargs) -> Optional[T]:
        try:
            db_obj = db.query(cls.model).filter(cls.model.id == obj_id).first()
            if db_obj:
                kwargs, force_null_fields = cls._normalize_kwargs(db, kwargs)
                # Filter out protected fields that should not be updated manually via kwargs
                protected_fields = {"id", "created_at", "updated_at", "deleted_at"}
                update_source = kwargs.pop("updated_by", None) or "System"
                applied_changes = False
                for key, value in kwargs.items():
                    if key not in protected_fields and hasattr(db_obj, key) and (value is not None or key in force_null_fields):
                        setattr(db_obj, key, value)
                        applied_changes = True
                if hasattr(db_obj, "updated_by"):
                    setattr(db_obj, "updated_by", update_source)
                if not applied_changes and not hasattr(db_obj, "updated_by"):
                    return db_obj
                db_obj.updated_at = get_kst_now_naive()
                db.commit()
                db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating {cls.model.__name__} {obj_id}: {e}")
            raise e

    @classmethod
    def delete(cls, db: Session, obj_id: str) -> bool:
        try:
            db_obj = db.query(cls.model).filter(cls.model.id == obj_id).first()
            if db_obj:
                db.delete(db_obj)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting {cls.model.__name__} {obj_id}: {e}")
            return False

    @classmethod
    def restore(cls, db: Session, obj_id: str) -> bool:
        try:
            db_obj = db.query(cls.model).filter(cls.model.id == obj_id).first()
            if db_obj:
                db_obj.deleted_at = None
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error restoring {cls.model.__name__} {obj_id}: {e}")
            return False
