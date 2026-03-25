from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Product
from .base_service import BaseService
from backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class ProductService(BaseService[Product]):
    model = Product
    object_name = "Product"

    @classmethod
    @handle_agent_errors
    def create_product(cls, db: Session, **kwargs) -> Product:
        try:
            return cls.create(db, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in create_product: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def update_product(cls, db: Session, product_id: str, **kwargs) -> Optional[Product]:
        try:
            return cls.update(db, product_id, **kwargs)
        except Exception as e:
            logger.error(f"Critical error in update_product: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def delete_product(cls, db: Session, product_id: str) -> bool:
        try:
            return cls.delete(db, product_id)
        except Exception as e:
            logger.error(f"Critical error in delete_product: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def restore_product(cls, db: Session, product_id: str) -> bool:
        try:
            return cls.restore(db, product_id)
        except Exception as e:
            logger.error(f"Critical error in restore_product: {e}")
            raise e

    @classmethod
    @handle_agent_errors
    def get_products(cls, db: Session) -> List[Product]:
        try:
            return cls.list(db)
        except Exception as e:
            logger.error(f"Error in get_products: {e}")
            return []

    @classmethod
    @handle_agent_errors
    def get_product(cls, db: Session, product_id: str) -> Optional[Product]:
        try:
            return cls.get(db, product_id)
        except Exception as e:
            logger.error(f"Error in get_product: {e}")
            return None
