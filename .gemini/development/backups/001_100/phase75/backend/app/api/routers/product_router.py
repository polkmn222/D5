from typing import Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from db.database import get_db
from backend.app.services.product_service import ProductService
from backend.app.services.model_service import ModelService
from backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from backend.app.services.vehicle_spec_service import VehicleSpecService as VehicleSpecificationService
from backend.app.core.templates import templates
from db.models import Product
import logging

from backend.app.core.toggles import is_feature_enabled
from backend.app.utils.error_handler import handle_agent_errors

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{product_id}")
@handle_agent_errors
async def product_detail(request: Request, product_id: str, db: Session = Depends(get_db)):
    if not is_feature_enabled("products"):
        return RedirectResponse(url="/?error=Coming+Soon")
    try:
        logger.info(f"Accessing Product Detail: {product_id}")
        product = ProductService.get_product(db, product_id)
        if not product: return RedirectResponse(url="/products?error=Product+not+found")
        
        brand_spec = BrandService.get_vehicle_spec(db, product.brand) if product.brand else None
        model_spec = ModelService.get_model(db, product.model) if product.model else None
        
        details = {
            "Name": product.name if product.name else "",
            "Brand": brand_spec.name if brand_spec else (product.brand if product.brand else ""),
            "Brand_Hidden_Ref": product.brand if product.brand else "",
            "Model": model_spec.name if model_spec else "",
            "Model_Hidden_Ref": product.model if product.model else "",
            "Category": product.category if product.category else "",
            "Price": product.base_price if product.base_price else 0,
            "Description": product.description if product.description else ""
        }
        return templates.TemplateResponse(request, "products/detail_view.html", {
            "request": request, "object_type": "Product", "plural_type": "products",
            "record_id": product_id, "record_name": product.name if product.name else "",
            "details": details, "created_at": product.created_at, "updated_at": product.updated_at,
            "related_lists": []
        })
    except Exception as e:
        logger.error(f"Error loading product detail: {e}")
        return RedirectResponse(url=f"/products?error=Error+loading+product+detail:+{str(e).replace(' ', '+')}")

@router.get("/", response_class=HTMLResponse)
@handle_agent_errors
async def list_products(request: Request, db: Session = Depends(get_db)):
    if not is_feature_enabled("products"):
        return RedirectResponse(url="/?error=Coming+Soon")
    try:
        products = ProductService.get_products(db)
        items = []
        for p in products:
            brand = VehicleSpecificationService.get_vehicle_spec(db, p.brand) if (hasattr(p, 'brand') and p.brand) else None
            model = ModelService.get_model(db, p.model) if (hasattr(p, 'model') and p.model) else None
            items.append({
                "id": p.id,
                "name": p.name if p.name else "",
                "brand": brand.name if brand else (p.brand if hasattr(p, 'brand') and p.brand else ""),
                "model": model.name if model else "",
                "base_price": p.base_price if p.base_price else 0,
                "category": p.category if p.category else "",
                "edit_url": f"/products/new-modal?id={p.id}"
            })
        columns = ["name", "brand", "model", "base_price", "category"]
        return templates.TemplateResponse(request, "products/list_view.html", {
            "request": request, 
            "object_type": "Product", 
            "plural_type": "products",
            "items": items, 
            "columns": columns
        })
    except Exception as e:
        logger.error(f"List products error: {e}")
        return RedirectResponse(url="/?error=Error+loading+products")

@router.post("/")
async def create_product(
    name: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    base_price: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        product = ProductService.create_product(
            db, name=name, brand=brand, model=model, category=category, base_price=base_price, description=description
        )
        return RedirectResponse(url=f"/products/{product.id}?success=Product+created+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        return RedirectResponse(url=f"/products?error=Error+creating+product:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{product_id}")
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    model: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    base_price: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        ProductService.update_product(
            db, product_id, name=name, brand=brand, model=model, category=category, base_price=base_price, description=description
        )
        return RedirectResponse(url=f"/products/{product_id}?success=Product+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        return RedirectResponse(url=f"/products/{product_id}?error=Error+updating+product:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{product_id}/delete")
async def delete_product(request: Request, product_id: str, db: Session = Depends(get_db)):
    try:
        ProductService.delete_product(db, product_id)
        if "application/json" in request.headers.get("Accept", ""):
            return {"status": "success", "message": "Record deleted successfully"}
        return RedirectResponse(url="/products?success=Record+deleted+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Delete Product error: {e}")
        return RedirectResponse(url=f"/products?error=Error+deleting+product:+{str(e).replace(' ', '+')}", status_code=303)
