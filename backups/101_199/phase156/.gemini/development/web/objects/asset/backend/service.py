from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Asset, Model, Product, Opportunity
from web.core.backend.utils.sf_id import get_id
from web.core.backend.utils.timezone import get_kst_now_naive
from web.core.backend.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class AssetService:
    """
    AssetService handles all business logic for the Asset object.
    All methods are static and wrapped in try-except blocks.
    """

    @staticmethod
    def _get_active_model(db: Session, model_id: Optional[str]) -> Optional[Model]:
        try:
            if not model_id: return None
            return db.query(Model).filter(Model.id == model_id, Model.deleted_at == None).first()
        except Exception as e:
            logger.error(f"Error fetching active model {model_id}: {str(e)}")
            return None

    @staticmethod
    def _get_active_product(db: Session, product_id: Optional[str]) -> Optional[Product]:
        try:
            if not product_id: return None
            return db.query(Product).filter(Product.id == product_id, Product.deleted_at == None).first()
        except Exception as e:
            logger.error(f"Error fetching active product {product_id}: {str(e)}")
            return None

    @staticmethod
    def _normalize_lookup_dependencies(db: Session, current: Optional[Asset], kwargs: dict) -> dict:
        try:
            normalized = dict(kwargs)
            force_null_fields = set(normalized.pop("_force_null_fields", []) or [])
            if "product" in normalized:
                product_id = normalized.get("product")
                if product_id:
                    product = AssetService._get_active_product(db, product_id)
                    if product:
                        normalized["model"] = product.model
                        if product.model:
                            model = AssetService._get_active_model(db, product.model)
                            normalized["brand"] = model.brand if model and model.brand else product.brand
                        else:
                            normalized["brand"] = product.brand
                else:
                    normalized["product"] = None
                    force_null_fields.add("product")
            if "model" in normalized:
                model_id = normalized.get("model")
                if model_id:
                    model = AssetService._get_active_model(db, model_id)
                    if model:
                        normalized["brand"] = model.brand
                        product_id = normalized.get("product", current.product if current else None)
                        if product_id:
                            product = AssetService._get_active_product(db, product_id)
                            if not product or product.model != model.id:
                                normalized["product"] = None
                                force_null_fields.add("product")
                else:
                    normalized["model"] = None
                    force_null_fields.add("model")
                    normalized["product"] = None
                    force_null_fields.add("product")
            if "brand" in normalized:
                brand_id = normalized.get("brand")
                if brand_id:
                    model_id = normalized.get("model", current.model if current else None)
                    if model_id:
                        model = AssetService._get_active_model(db, model_id)
                        if not model or model.brand != brand_id:
                            normalized["model"] = None
                            force_null_fields.add("model")
                            normalized["product"] = None
                            force_null_fields.add("product")
                    product_id = normalized.get("product", current.product if current else None)
                    if product_id:
                        product = AssetService._get_active_product(db, product_id)
                        if not product or product.brand != brand_id:
                            normalized["product"] = None
                            force_null_fields.add("product")
                else:
                    normalized["brand"] = None
                    force_null_fields.add("brand")
                    normalized["model"] = None
                    force_null_fields.add("model")
                    normalized["product"] = None
                    force_null_fields.add("product")
            if force_null_fields:
                normalized["_force_null_fields"] = sorted(force_null_fields)
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing lookup dependencies: {str(e)}")
            return kwargs

    @staticmethod
    @handle_agent_errors
    def create_asset(db: Session, **kwargs) -> Optional[Asset]:
        try:
            clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
            if not clean_kwargs.get("name"): clean_kwargs["name"] = clean_kwargs.get("vin", "New Asset")
            asset = Asset(
                id=get_id("Asset"),
                created_at=get_kst_now_naive(),
                updated_at=get_kst_now_naive(),
                **clean_kwargs
            )
            db.add(asset)
            db.commit()
            db.refresh(asset)
            return asset
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create asset: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def get_assets(db: Session, contact: Optional[str] = None) -> List[Asset]:
        try:
            query = db.query(Asset).filter(Asset.deleted_at == None)
            if contact: query = query.filter(Asset.contact == contact)
            return query.all()
        except Exception as e:
            logger.error(f"Failed to get assets: {str(e)}")
            return []

    @staticmethod
    @handle_agent_errors
    def get_asset(db: Session, asset_id: str) -> Optional[Asset]:
        try:
            return db.query(Asset).filter(
                Asset.id == asset_id,
                Asset.deleted_at == None
            ).first()
        except Exception as e:
            logger.error(f"Failed to get asset {asset_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def update_asset(db: Session, asset_id: str, **kwargs) -> Optional[Asset]:
        try:
            asset = AssetService.get_asset(db, asset_id)
            if not asset: return None
            normalized_kwargs = AssetService._normalize_lookup_dependencies(db, asset, kwargs)
            force_null_fields = normalized_kwargs.pop("_force_null_fields", [])
            for key, value in normalized_kwargs.items():
                if hasattr(asset, key): setattr(asset, key, value)
            for field in force_null_fields:
                if hasattr(asset, field): setattr(asset, field, None)
            asset.updated_at = get_kst_now_naive()
            db.commit()
            db.refresh(asset)
            return asset
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update asset {asset_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def delete_asset(db: Session, asset_id: str, hard_delete: bool = False) -> bool:
        try:
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset: return False
            if hard_delete:
                db.query(Opportunity).filter(Opportunity.asset == asset_id).delete(synchronize_session=False)
                db.delete(asset)
            else:
                asset.deleted_at = get_kst_now_naive()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete asset {asset_id}: {str(e)}")
            return False

    @staticmethod
    @handle_agent_errors
    def restore_asset(db: Session, asset_id: str) -> bool:
        try:
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset: return False
            asset.deleted_at = None
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to restore asset {asset_id}: {str(e)}")
            return False
