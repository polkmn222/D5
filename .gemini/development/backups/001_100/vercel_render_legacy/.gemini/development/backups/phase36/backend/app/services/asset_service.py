from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Asset
from .base_service import BaseService
from backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class AssetService(BaseService[Asset]):
    model = Asset
    object_name = "Asset"

    @classmethod
    @handle_agent_errors
    def create_asset(cls, db: Session, name: str, contact: Optional[str] = None, product: Optional[str] = None, **kwargs) -> Asset:
        try:
            return cls.create(db, name=name, contact=contact, product=product, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in create_asset: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def get_assets(cls, db: Session, contact: Optional[str] = None) -> List[Asset]:
        try:
            return cls.list(db, contact=contact)
        except Exception as e:
            logger.error(f"Error in get_assets: {e}")
            return []

    @classmethod
    @handle_agent_errors
    def get_asset(cls, db: Session, asset_id: str) -> Optional[Asset]:
        try:
            return cls.get(db, asset_id)
        except Exception as e:
            logger.error(f"Error in get_asset: {e}")
            return None

    @classmethod
    @handle_agent_errors
    def update_asset(cls, db: Session, asset_id: str, **kwargs) -> Optional[Asset]:
        try:
            return cls.update(db, asset_id, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in update_asset: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def delete_asset(cls, db: Session, asset_id: str) -> bool:
        try:
            return cls.delete(db, asset_id)
        except Exception as e:
            logger.error(f"Critical error in delete_asset: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def restore_asset(cls, db: Session, asset_id: str) -> bool:
        try:
            return cls.restore(db, asset_id)
        except Exception as e:
            logger.error(f"Critical error in restore_asset: {e}")
            raise e
