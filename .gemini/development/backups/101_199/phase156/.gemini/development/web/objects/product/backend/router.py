from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import logging

from db.database import get_db
from db.models import Asset, Lead, Opportunity, Product, Model, VehicleSpecification
from web.objects.product.backend.service import ProductService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.core.backend.core.templates import templates
from web.core.backend.utils.error_handler import handle_agent_errors
from web.core.backend.core.toggles import is_feature_enabled

logger = logging.getLogger(__name__)

class ProductRouter:
    """
    ProductRouter manages all routes for the Product object.
    It uses a single APIRouter instance and defines routes as class methods.
    """
    router = APIRouter()
    PRODUCT_LIST_COLUMNS = ["name", "brand", "model", "base_price", "category"]
    PRODUCT_LIST_BUILTINS = (
        {"id": "product-all", "label": "All Products", "source": "all"},
        {"id": "product-recent", "label": "Recently Viewed", "source": "recent"},
    )

    @staticmethod
    @router.get("/views")
    @handle_agent_errors
    async def list_product_views(db: Session = Depends(get_db)):
        try:
            views = LeadListViewService.list_views(
                db,
                ProductRouter.PRODUCT_LIST_COLUMNS,
                object_type="Product",
                builtin_views=ProductRouter.PRODUCT_LIST_BUILTINS,
            )
            pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
            return {"views": views, "pinned_view_id": pinned_view_id}
        except Exception as e:
            logger.error(f"Error listing product views: {str(e)}")
            return {"views": [], "pinned_view_id": None}

    @staticmethod
    @router.post("/views")
    @handle_agent_errors
    async def create_product_view(payload: dict = Body(...), db: Session = Depends(get_db)):
        try:
            view = LeadListViewService.create_view(
                db,
                payload,
                ProductRouter.PRODUCT_LIST_COLUMNS,
                object_type="Product",
                builtin_views=ProductRouter.PRODUCT_LIST_BUILTINS,
            )
            return JSONResponse(content={"status": "success", "view": view})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error creating product view: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.put("/views/{view_id}")
    @handle_agent_errors
    async def update_product_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
        try:
            view = LeadListViewService.update_view(
                db,
                view_id,
                payload,
                ProductRouter.PRODUCT_LIST_COLUMNS,
                object_type="Product",
                builtin_views=ProductRouter.PRODUCT_LIST_BUILTINS,
            )
            return JSONResponse(content={"status": "success", "view": view})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error updating product view {view_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.delete("/views/{view_id}")
    @handle_agent_errors
    async def delete_product_view(view_id: str, db: Session = Depends(get_db)):
        try:
            LeadListViewService.delete_view(db, view_id, object_type="Product")
            return JSONResponse(content={"status": "success"})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error deleting product view {view_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.post("/views/{view_id}/pin")
    @handle_agent_errors
    async def pin_product_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
        try:
            payload = payload or {}
            pinned_view_id = LeadListViewService.set_pinned_view(
                db,
                view_id,
                ProductRouter.PRODUCT_LIST_COLUMNS,
                pinned=bool(payload.get("pinned", True)),
                object_type="Product",
                builtin_views=ProductRouter.PRODUCT_LIST_BUILTINS,
            )
            return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error pinning product view {view_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.get("/{product_id}", response_class=HTMLResponse)
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

            related_lists = []
            assets = db.query(Asset).filter(Asset.product == product_id, Asset.deleted_at == None).all()
            if assets:
                related_lists.append({
                    "title": "Assets",
                    "icon": "asset",
                    "columns": ["Name", "Vin", "Status"],
                    "new_url": f"/assets/new-modal?product={product_id}",
                    "view_all_url": f"/assets?product={product_id}&related=1&back_to=/products/{product_id}?tab=related",
                    "total_count": len(assets),
                    "items": [{"name": a.name or "", "vin": a.vin or "", "status": a.status or "", "_href": f"/assets/{a.id}"} for a in assets[:5]],
                })

            opportunities = db.query(Opportunity).filter(Opportunity.product == product_id, Opportunity.deleted_at == None).all()
            if opportunities:
                related_lists.append({
                    "title": "Opportunities",
                    "icon": "opportunity",
                    "columns": ["Name", "Stage", "Amount"],
                    "new_url": f"/opportunities/new-modal?product={product_id}",
                    "view_all_url": f"/opportunities?product={product_id}&related=1&back_to=/products/{product_id}?tab=related",
                    "total_count": len(opportunities),
                    "items": [{"name": o.name or "", "stage": o.stage or "", "amount": f"{o.amount:,}" if o.amount else "0", "_href": f"/opportunities/{o.id}"} for o in opportunities[:5]],
                })

            leads = db.query(Lead).filter(Lead.product == product_id, Lead.deleted_at == None, Lead.is_converted == False).all()
            if leads:
                related_lists.append({
                    "title": "Leads",
                    "icon": "lead",
                    "columns": ["Name", "Email", "Phone"],
                    "new_url": f"/leads/new-modal?product={product_id}",
                    "view_all_url": f"/leads?product={product_id}&related=1&back_to=/products/{product_id}?tab=related",
                    "total_count": len(leads),
                    "items": [{"name": f"{l.first_name if l.first_name else ''} {l.last_name if l.last_name else ''}".strip(), "email": l.email or "", "phone": l.phone or "", "_href": f"/leads/{l.id}"} for l in leads[:5]],
                })

            if model_spec:
                related_lists.append({
                    "title": "Model",
                    "icon": "model",
                    "columns": ["Name", "Description"],
                    "view_all_url": f"/models?id={model_spec.id}&related=1&back_to=/products/{product_id}?tab=related",
                    "total_count": 1,
                    "items": [{"name": model_spec.name or "", "description": model_spec.description or "", "_href": f"/models/{model_spec.id}"}],
                })

            if brand_spec:
                related_lists.append({
                    "title": "Brand",
                    "icon": "brand",
                    "columns": ["Name", "Type"],
                    "view_all_url": f"/vehicle_specifications?id={brand_spec.id}&related=1&back_to=/products/{product_id}?tab=related",
                    "total_count": 1,
                    "items": [{"name": brand_spec.name or "", "type": brand_spec.record_type or "", "_href": f"/vehicle_specifications/{brand_spec.id}"}],
                })

            return templates.TemplateResponse(request, "product/detail_view.html", {
                "request": request, "object_type": "Product", "plural_type": "products",
                "record_id": product_id, "record_name": product.name if product.name else "",
                "details": details, "created_at": product.created_at, "updated_at": product.updated_at,
                "related_lists": related_lists
            })
        except Exception as e:
            logger.error(f"Error rendering product detail {product_id}: {str(e)}")
            return RedirectResponse(url="/products?error=Internal+server+error")

    @staticmethod
    @router.get("/", response_class=HTMLResponse)
    @handle_agent_errors
    async def list_products(request: Request, db: Session = Depends(get_db)):
        if not is_feature_enabled("products"):
            return RedirectResponse(url="/?error=Coming+Soon")
        try:
            related_mode = request.query_params.get("related") == "1" or bool(request.query_params.get("back_to"))
            back_url = request.query_params.get("back_to") or "/products"
            filters = [Product.deleted_at == None]
            record_id = request.query_params.get("id")
            if record_id:
                filters.append(Product.id == record_id)
                related_mode = True
            for key in ["brand", "model"]:
                value = request.query_params.get(key)
                if value:
                    filters.append(getattr(Product, key) == value)
                    related_mode = True
            products = (
                db.query(Product)
                .filter(*filters)
                .order_by(Product.name.asc())
                .all()
            )
            brand_ids = {p.brand for p in products if getattr(p, 'brand', None)}
            model_ids = {p.model for p in products if getattr(p, 'model', None)}
            brand_map = {}
            model_map = {}
            if brand_ids:
                brand_map = {brand.id: brand for brand in db.query(VehicleSpecification).filter(VehicleSpecification.id.in_(brand_ids), VehicleSpecification.deleted_at == None).all()}
            if model_ids:
                model_map = {model.id: model for model in db.query(Model).filter(Model.id.in_(model_ids), Model.deleted_at == None).all()}
            items = []
            for p in products:
                brand = brand_map.get(p.brand) if (hasattr(p, 'brand') and p.brand) else None
                model = model_map.get(p.model) if (hasattr(p, 'model') and p.model) else None
                items.append({
                    "id": p.id,
                    "name": p.name if p.name else "",
                    "brand": brand.name if brand else (p.brand if hasattr(p, 'brand') and p.brand else ""),
                    "model": model.name if model else "",
                    "base_price": p.base_price if p.base_price else 0,
                    "category": p.category if p.category else "",
                    "edit_url": f"/products/new-modal?id={p.id}",
                    "_href": f"/products/{p.id}"
                })
            
            if related_mode:
                new_query = []
                for key in ["brand", "model"]:
                    value = request.query_params.get(key)
                    if value:
                        new_query.append(f"{key}={value}")
                new_url = "/products/new-modal"
                if new_query:
                    new_url += "?" + "&".join(new_query)
                return templates.TemplateResponse(request, "related/list_view.html", {
                    "request": request,
                    "page_title": "Products",
                    "items": items,
                    "columns": ProductRouter.PRODUCT_LIST_COLUMNS,
                    "back_url": back_url,
                    "new_url": new_url,
                    "page_icon": "product",
                    "show_actions": True,
                })
            
            saved_views = LeadListViewService.list_views(
                db,
                ProductRouter.PRODUCT_LIST_COLUMNS,
                object_type="Product",
                builtin_views=ProductRouter.PRODUCT_LIST_BUILTINS,
            )
            saved_view_ids = {view["id"] for view in saved_views}
            pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
            requested_view = request.query_params.get("view")
            current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "product-all")
            
            return templates.TemplateResponse(request, "product/list_view.html", {
                "request": request, 
                "object_type": "Product", 
                "plural_type": "products",
                "items": items, 
                "columns": ProductRouter.PRODUCT_LIST_COLUMNS,
                "current_view": current_view,
                "list_view_options": [{"value": view["id"], "label": view["label"]} for view in saved_views],
                "saved_views": saved_views,
                "pinned_view_id": pinned_view_id,
                "list_view_storage_key": "d4_recent_products",
            })
        except Exception as e:
            logger.error(f"Error listing products: {str(e)}")
            return RedirectResponse(url="/?error=Internal+server+error")

    @staticmethod
    @router.post("/")
    @handle_agent_errors
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
            logger.error(f"Error creating product: {str(e)}")
            return RedirectResponse(url="/products?error=Failed+to+create+record", status_code=303)

    @staticmethod
    @router.post("/{product_id}")
    @handle_agent_errors
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
            logger.error(f"Error updating product {product_id}: {str(e)}")
            return RedirectResponse(url=f"/products/{product_id}?error=Failed+to+update+record", status_code=303)

    @staticmethod
    @router.post("/{product_id}/delete")
    @handle_agent_errors
    async def delete_product(request: Request, product_id: str, db: Session = Depends(get_db)):
        try:
            ProductService.delete_product(db, product_id)
            if "application/json" in request.headers.get("Accept", ""):
                return {"status": "success", "message": "Record deleted successfully"}
            return RedirectResponse(url="/products?success=Record+deleted+successfully", status_code=303)
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {str(e)}")
            return RedirectResponse(url="/products?error=Failed+to+delete+record", status_code=303)
