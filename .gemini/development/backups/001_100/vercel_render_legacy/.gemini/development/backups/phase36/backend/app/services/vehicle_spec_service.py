from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import VehicleSpecification
from .base_service import BaseService

logger = logging.getLogger(__name__)

class VehicleSpecService(BaseService[VehicleSpecification]):
    model = VehicleSpecification
    object_name = "VehicleSpecification"

    @classmethod
    def create_spec(cls, db: Session, **kwargs) -> VehicleSpecification:
        try:
            return cls.create(db, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in create_spec: {e}")
            raise e

    @classmethod
    def update_vehicle_spec(cls, db: Session, spec_id: str, **kwargs) -> Optional[VehicleSpecification]:
        try:
            return cls.update(db, spec_id, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in update_vehicle_spec: {e}")
            raise e

    @classmethod
    def delete_vehicle_spec(cls, db: Session, spec_id: str) -> bool:
        try:
            return cls.delete(db, spec_id)
        except Exception as e:
            logger.error(f"Critical error in delete_vehicle_spec: {e}")
            raise e

    @classmethod
    def get_vehicle_specs(cls, db: Session, record_type: Optional[str] = None) -> List[VehicleSpecification]:
        try:
            return cls.list(db, record_type=record_type)
        except Exception as e:
            logger.error(f"Error in get_vehicle_specs: {e}")
            return []

    @classmethod
    def get_vehicle_spec(cls, db: Session, spec_id: str) -> Optional[VehicleSpecification]:
        try:
            return cls.get(db, spec_id)
        except Exception as e:
            logger.error(f"Error in get_vehicle_spec: {e}")
            return None
