from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Product, Opportunity, Asset, Lead
from web.core.backend.utils.sf_id import get_id
from web.core.backend.utils.timezone import get_kst_now_naive
from web.core.backend.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class ProductService:
    """
    ProductService handles all business logic for the Product object.
    All methods are static and wrapped in try-except blocks.
    """

    @staticmethod
    @handle_agent_errors
    def create_product(db: Session, **kwargs) -> Optional[Product]:
        try:
            clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
            product = Product(
                id=get_id("Product"),
                created_at=get_kst_now_naive(),
                updated_at=get_kst_now_naive(),
                **clean_kwargs
            )
            db.add(product)
            db.commit()
            db.refresh(product)
            return product
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create product: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def get_products(db: Session) -> List[Product]:
        try:
            return db.query(Product).filter(Product.deleted_at == None).all()
        except Exception as e:
            logger.error(f"Failed to list products: {str(e)}")
            return []

    @staticmethod
    @handle_agent_errors
    def get_product(db: Session, product_id: str) -> Optional[Product]:
        try:
            return db.query(Product).filter(
                Product.id == product_id,
                Product.deleted_at == None
            ).first()
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def update_product(db: Session, product_id: str, **kwargs) -> Optional[Product]:
        try:
            product = ProductService.get_product(db, product_id)
            if not product: return None
            force_null_fields = kwargs.pop("_force_null_fields", []) or []
            for key, value in kwargs.items():
                if hasattr(product, key): setattr(product, key, value)
            for field in force_null_fields:
                if hasattr(product, field): setattr(product, field, None)
            product.updated_at = get_kst_now_naive()
            db.commit()
            db.refresh(product)
            return product
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update product {product_id}: {str(e)}")
            return None

    @staticmethod
    @handle_agent_errors
    def delete_product(db: Session, product_id: str, hard_delete: bool = False) -> bool:
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product: return False
            if hard_delete:
                db.query(Opportunity).filter(Opportunity.product == product_id).delete(synchronize_session=False)
                asset_ids = [row.id for row in db.query(Asset.id).filter(Asset.product == product_id).all()]
                if asset_ids:
                    db.query(Opportunity).filter(Opportunity.asset.in_(asset_ids)).delete(synchronize_session=False)
                    db.query(Asset).filter(Asset.id.in_(asset_ids)).delete(synchronize_session=False)
                db.query(Lead).filter(Lead.product == product_id).delete(synchronize_session=False)
                db.delete(product)
            else:
                product.deleted_at = get_kst_now_naive()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete product {product_id}: {str(e)}")
            return False

    @staticmethod
    @handle_agent_errors
    def restore_product(db: Session, product_id: str) -> bool:
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product: return False
            product.deleted_at = None
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to restore product {product_id}: {str(e)}")
            return False
