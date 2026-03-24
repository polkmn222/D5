from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Model
from .base_service import BaseService

logger = logging.getLogger(__name__)

class ModelService(BaseService[Model]):
    model = Model
    object_name = "Model"

    @classmethod
    def create_model(cls, db: Session, **kwargs) -> Model:
        try:
            return cls.create(db, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in create_model: {e}")
            raise e

    @classmethod
    def get_models(cls, db: Session) -> List[Model]:
        try:
            return cls.list(db)
        except Exception as e:
            logger.error(f"Error in get_models: {e}")
            return []

    @classmethod
    def get_model(cls, db: Session, model_id: str) -> Optional[Model]:
        try:
            return cls.get(db, model_id)
        except Exception as e:
            logger.error(f"Error in get_model: {e}")
            return None

    @classmethod
    def update_model(cls, db: Session, model_id: str, **kwargs) -> Optional[Model]:
        try:
            return cls.update(db, model_id, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in update_model: {e}")
            raise e

    @classmethod
    def delete_model(cls, db: Session, model_id: str) -> bool:
        try:
            return cls.delete(db, model_id)
        except Exception as e:
            logger.error(f"Critical error in delete_model: {e}")
            raise e
