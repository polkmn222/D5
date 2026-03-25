from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from db.database import get_db
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as VehicleSpecificationService
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.backend.app.core.templates import templates
from db.models import Product
import logging

from web.backend.app.core.toggles import is_feature_enabled
from web.backend.app.utils.error_handler import handle_agent_errors

router = APIRouter()
logger = logging.getLogger(__name__)
PRODUCT_LIST_COLUMNS = ["name", "brand", "model", "base_price", "category"]
PRODUCT_LIST_BUILTINS = (
    {"id": "product-all", "label": "All Products", "source": "all"},
    {"id": "product-recent", "label": "Recently Viewed", "source": "recent"},
)


@router.get("/views")
@handle_agent_errors
async def list_product_views(db: Session = Depends(get_db)):
    views = LeadListViewService.list_views(
        db,
        PRODUCT_LIST_COLUMNS,
        object_type="Product",
        builtin_views=PRODUCT_LIST_BUILTINS,
    )
    pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
    return {"views": views, "pinned_view_id": pinned_view_id}


@router.post("/views")
@handle_agent_errors
async def create_product_view(payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.create_view(
            db,
            payload,
            PRODUCT_LIST_COLUMNS,
            object_type="Product",
            builtin_views=PRODUCT_LIST_BUILTINS,
        )
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.put("/views/{view_id}")
@handle_agent_errors
async def update_product_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.update_view(
            db,
            view_id,
            payload,
            PRODUCT_LIST_COLUMNS,
            object_type="Product",
            builtin_views=PRODUCT_LIST_BUILTINS,
        )
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.delete("/views/{view_id}")
@handle_agent_errors
async def delete_product_view(view_id: str, db: Session = Depends(get_db)):
    try:
        LeadListViewService.delete_view(db, view_id, object_type="Product")
        return JSONResponse(content={"status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.post("/views/{view_id}/pin")
@handle_agent_errors
async def pin_product_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
    payload = payload or {}
    try:
        pinned_view_id = LeadListViewService.set_pinned_view(
            db,
            view_id,
            PRODUCT_LIST_COLUMNS,
            pinned=bool(payload.get("pinned", True)),
            object_type="Product",
            builtin_views=PRODUCT_LIST_BUILTINS,
        )
        return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})

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
        saved_views = LeadListViewService.list_views(
            db,
            PRODUCT_LIST_COLUMNS,
            object_type="Product",
            builtin_views=PRODUCT_LIST_BUILTINS,
        )
        saved_view_ids = {view["id"] for view in saved_views}
        pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
        requested_view = request.query_params.get("view")
        current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "product-all")
        return templates.TemplateResponse(request, "products/list_view.html", {
            "request": request, 
            "object_type": "Product", 
            "plural_type": "products",
            "items": items, 
            "columns": PRODUCT_LIST_COLUMNS,
            "current_view": current_view,
            "list_view_options": [{"value": view["id"], "label": view["label"]} for view in saved_views],
            "saved_views": saved_views,
            "pinned_view_id": pinned_view_id,
            "list_view_storage_key": "d4_recent_products",
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
