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
    def create(cls, db: Session, **kwargs) -> T:
        try:
            obj_id = get_id(cls.object_name)
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
                # Filter out protected fields that should not be updated manually via kwargs
                protected_fields = {"id", "created_at", "updated_at", "deleted_at"}
                for key, value in kwargs.items():
                    # CRITICAL FIX: Only update if value is NOT None. 
                    # FastAPI routers pass None for missing optional Form fields, which wipes data.
                    if key not in protected_fields and hasattr(db_obj, key) and value is not None:
                        setattr(db_obj, key, value)
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
                db_obj.deleted_at = get_kst_now_naive()
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
