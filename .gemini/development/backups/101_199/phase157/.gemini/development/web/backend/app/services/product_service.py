from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from db.models import Product
from web.backend.app.utils.sf_id import get_id
from web.backend.app.utils.timezone import get_kst_now_naive
from web.backend.app.utils.error_handler import handle_agent_errors

logger = logging.getLogger(__name__)

class ProductService:
    @staticmethod
    @handle_agent_errors
    def create_product(db: Session, **kwargs) -> Optional[Product]:
        clean_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
        product = Product(id=get_id('Product'), created_at=get_kst_now_naive(), updated_at=get_kst_now_naive(), **clean_kwargs)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    @handle_agent_errors
    def get_products(db: Session) -> List[Product]:
        return db.query(Product).filter(Product.deleted_at == None).all()

    @staticmethod
    @handle_agent_errors
    def get_product(db: Session, product_id: str) -> Optional[Product]:
        return db.query(Product).filter(Product.id == product_id, Product.deleted_at == None).first()

    @staticmethod
    @handle_agent_errors
    def update_product(db: Session, product_id: str, **kwargs) -> Optional[Product]:
        product = ProductService.get_product(db, product_id)
        if not product: return None
        for key, value in kwargs.items():
            if hasattr(product, key): setattr(product, key, value)
        product.updated_at = get_kst_now_naive()
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    @handle_agent_errors
    def delete_product(db: Session, product_id: str, hard_delete: bool = False) -> bool:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product: return False
        if hard_delete: db.delete(product)
        else: product.deleted_at = get_kst_now_naive()
        db.commit()
        return True
