from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Asset, Model, Product
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.timezone import get_kst_now_naive
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class AssetService:
    @staticmethod
    @handle_agent_errors
    def create_asset(db: Session, **kwargs) -> Optional[Asset]:
        clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
        asset = Asset(id=get_id("Asset"), created_at=get_kst_now_naive(), updated_at=get_kst_now_naive(), **clean_kwargs)
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    @handle_agent_errors
    def get_assets(db: Session, contact: Optional[str] = None) -> List[Asset]:
        query = db.query(Asset).filter(Asset.deleted_at == None)
        if contact:
            query = query.filter(Asset.contact == contact)
        return query.all()

    @staticmethod
    @handle_agent_errors
    def get_asset(db: Session, asset_id: str) -> Optional[Asset]:
        return db.query(Asset).filter(Asset.id == asset_id, Asset.deleted_at == None).first()

    @staticmethod
    @handle_agent_errors
    def update_asset(db: Session, asset_id: str, **kwargs) -> Optional[Asset]:
        asset = AssetService.get_asset(db, asset_id)
        if not asset: return None
        for key, value in kwargs.items():
            if hasattr(asset, key): setattr(asset, key, value)
        asset.updated_at = get_kst_now_naive()
        db.commit()
        db.refresh(asset)
        return asset

    @staticmethod
    @handle_agent_errors
    def delete_asset(db: Session, asset_id: str, hard_delete: bool = False) -> bool:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset: return False
        if hard_delete: db.delete(asset)
        else: asset.deleted_at = get_kst_now_naive()
        db.commit()
        return True
