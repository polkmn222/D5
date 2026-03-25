from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import VehicleSpecification
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.timezone import get_kst_now_naive
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class VehicleSpecService:
    @staticmethod
    @handle_agent_errors
    def create_spec(db: Session, **kwargs) -> Optional[VehicleSpecification]:
        clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
        spec = VehicleSpecification(id=get_id('VehicleSpecification'), created_at=get_kst_now_naive(), updated_at=get_kst_now_naive(), **clean_kwargs)
        db.add(spec)
        db.commit()
        db.refresh(spec)
        return spec

    @staticmethod
    @handle_agent_errors
    def get_vehicle_specs(db: Session, record_type: Optional[str] = None) -> List[VehicleSpecification]:
        query = db.query(VehicleSpecification).filter(VehicleSpecification.deleted_at == None)
        if record_type: query = query.filter(VehicleSpecification.record_type == record_type)
        return query.all()

    @staticmethod
    @handle_agent_errors
    def get_vehicle_spec(db: Session, spec_id: str) -> Optional[VehicleSpecification]:
        return db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id, VehicleSpecification.deleted_at == None).first()

    @staticmethod
    @handle_agent_errors
    def delete_vehicle_spec(db: Session, spec_id: str, hard_delete: bool = False) -> bool:
        spec = db.query(VehicleSpecification).filter(VehicleSpecification.id == spec_id).first()
        if not spec: return False
        if hard_delete: db.delete(spec)
        else: spec.deleted_at = get_kst_now_naive()
        db.commit()
        return True
