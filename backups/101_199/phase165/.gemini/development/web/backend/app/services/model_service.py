from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Model
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.timezone import get_kst_now_naive
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class ModelService:
    @staticmethod
    @handle_agent_errors
    def create_model(db: Session, **kwargs) -> Optional[Model]:
        clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
        model = Model(id=get_id('Model'), created_at=get_kst_now_naive(), updated_at=get_kst_now_naive(), **clean_kwargs)
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    @handle_agent_errors
    def get_models(db: Session) -> List[Model]:
        return db.query(Model).filter(Model.deleted_at == None).all()

    @staticmethod
    @handle_agent_errors
    def get_model(db: Session, model_id: str) -> Optional[Model]:
        return db.query(Model).filter(Model.id == model_id, Model.deleted_at == None).first()

    @staticmethod
    @handle_agent_errors
    def update_model(db: Session, model_id: str, **kwargs) -> Optional[Model]:
        model = ModelService.get_model(db, model_id)
        if not model: return None
        for key, value in kwargs.items():
            if hasattr(model, key): setattr(model, key, value)
        model.updated_at = get_kst_now_naive()
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    @handle_agent_errors
    def delete_model(db: Session, model_id: str, hard_delete: bool = False) -> bool:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model: return False
        if hard_delete: db.delete(model)
        else: model.deleted_at = get_kst_now_naive()
        db.commit()
        return True
