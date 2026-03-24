from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import VehicleSpecification, Model, Product, Asset, Opportunity, Lead
from web.core.backend.utils.sf_id import get_id
from web.core.backend.utils.timezone import get_kst_now_naive
from web.core.backend.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class VehicleSpecService:
    """
    VehicleSpecService handles all business logic for Brands (VehicleSpecification).
    All methods are static and wrapped in try-except blocks.
    """

    @staticmethod
    @handle_agent_errors
    def create_spec(db: Session, **kwargs) -> Optional[VehicleSpecification]:
        try:
            clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
            spec = VehicleSpecification(
                id=get_id("VehicleSpecification"),
                created_at=get_kst_now_naive(),
                updated_at=get_kst_now_naive(),
                **clean_kwargs
            )
            db.add(spec)
            db.commit()
            db.refresh(spec)
            return spec
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create vehicle spec: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def get_vehicle_specs(db: Session, record_type: Optional[str] = None) -> List[VehicleSpecification]:
        try:
            query = db.query(VehicleSpecification).filter(VehicleSpecification.deleted_at == None)
            if record_type:
                query = query.filter(VehicleSpecification.record_type == record_type)
            return query.all()
        except Exception as e:
            logger.error(f"Failed to get vehicle specs: {str(e)}")
            return []

    @staticmethod
    @handle_agent_errors
    def get_vehicle_spec(db: Session, spec_id: str) -> Optional[VehicleSpecification]:
        try:
            return db.query(VehicleSpecification).filter(
                VehicleSpecification.id == spec_id,
                VehicleSpecification.deleted_at == None
            ).first()
        except Exception as e:
            logger.error(f"Failed to get vehicle spec {spec_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def update_vehicle_spec(db: Session, spec_id: str, **kwargs) -> Optional[VehicleSpecification]:
        try:
            spec = VehicleSpecService.get_vehicle_spec(db, spec_id)
            if not spec:
                return None
            for key, value in kwargs.items():
                if hasattr(spec, key):
                    setattr(spec, key, value)
            spec.updated_at = get_kst_now_naive()
            db.commit()
            db.refresh(spec)
            return spec
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update vehicle spec {spec_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def delete_vehicle_spec(db: Session, spec_id: str, hard_delete: bool = False) -> bool:
        try:
            spec = db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id).first()
            if not spec:
                return False
            
            if hard_delete:
                # Hard delete cascading logic from RecordDeleteService
                db.query(Opportunity).filter(Opportunity.brand == spec_id).delete(synchronize_session=False)
                db.query(Asset).filter(Asset.brand == spec_id).delete(synchronize_session=False)
                db.query(Lead).filter(Lead.brand == spec_id).delete(synchronize_session=False)
                db.query(Product).filter(Product.brand == spec_id).delete(synchronize_session=False)
                db.query(Model).filter(Model.brand == spec_id).delete(synchronize_session=False)
                db.delete(spec)
            else:
                spec.deleted_at = get_kst_now_naive()
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete vehicle spec {spec_id}: {str(e)}")
            return False

    @staticmethod
    @handle_agent_errors
    def restore(db: Session, spec_id: str) -> bool:
        try:
            spec = db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id).first()
            if not spec:
                return False
            spec.deleted_at = None
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to restore vehicle spec {spec_id}: {str(e)}")
            return False

class ModelService:
    """
    ModelService handles all business logic for Models.
    All methods are static and wrapped in try-except blocks.
    """

    @staticmethod
    @handle_agent_errors
    def create_model(db: Session, **kwargs) -> Optional[Model]:
        try:
            clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
            model = Model(
                id=get_id("Model"),
                created_at=get_kst_now_naive(),
                updated_at=get_kst_now_naive(),
                **clean_kwargs
            )
            db.add(model)
            db.commit()
            db.refresh(model)
            return model
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create model: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def get_models(db: Session) -> List[Model]:
        try:
            return db.query(Model).filter(Model.deleted_at == None).all()
        except Exception as e:
            logger.error(f"Failed to get models: {str(e)}")
            return []

    @staticmethod
    @handle_agent_errors
    def get_model(db: Session, model_id: str) -> Optional[Model]:
        try:
            return db.query(Model).filter(
                Model.id == model_id,
                Model.deleted_at == None
            ).first()
        except Exception as e:
            logger.error(f"Failed to get model {model_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def update_model(db: Session, model_id: str, **kwargs) -> Optional[Model]:
        try:
            model = ModelService.get_model(db, model_id)
            if not model:
                return None
            for key, value in kwargs.items():
                if hasattr(model, key):
                    setattr(model, key, value)
            model.updated_at = get_kst_now_naive()
            db.commit()
            db.refresh(model)
            return model
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update model {model_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def delete_model(db: Session, model_id: str, hard_delete: bool = False) -> bool:
        try:
            model = db.query(Model).filter(Model.id == model_id).first()
            if not model:
                return False
            
            if hard_delete:
                db.query(Opportunity).filter(Opportunity.model == model_id).delete(synchronize_session=False)
                db.query(Asset).filter(Asset.model == model_id).delete(synchronize_session=False)
                db.query(Lead).filter(Lead.model == model_id).delete(synchronize_session=False)
                db.query(Product).filter(Product.model == model_id).delete(synchronize_session=False)
                db.delete(model)
            else:
                model.deleted_at = get_kst_now_naive()
            
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete model {model_id}: {str(e)}")
            return False
