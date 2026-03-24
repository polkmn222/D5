from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
import logging

from db.database import get_db
from db.models import Asset
from web.objects.asset.backend.service import AssetService
from web.objects.contact.backend.service import ContactService
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.core.backend.core.templates import templates
from web.core.backend.utils.error_handler import handle_agent_errors
from web.core.backend.core.toggles import is_feature_enabled

logger = logging.getLogger(__name__)

class AssetRouter:
    """
    AssetRouter manages all routes for the Asset object.
    It uses a single APIRouter instance and defines routes as class methods.
    """
    router = APIRouter()
    ASSET_LIST_COLUMNS = ["name", "vin", "price", "status"]
    ASSET_LIST_BUILTINS = (
        {"id": "asset-all", "label": "All Assets", "source": "all"},
        {"id": "asset-recent", "label": "Recently Viewed", "source": "recent"},
    )

    @staticmethod
    def _contact_display_name(contact) -> str:
        if not contact:
            return ""
        return f"{contact.first_name if contact.first_name else ''} {contact.last_name if contact.last_name else ''}".strip() or contact.name or ""

    @staticmethod
    @router.get("/views")
    @handle_agent_errors
    async def list_asset_views(db: Session = Depends(get_db)):
        try:
            views = LeadListViewService.list_views(
                db,
                AssetRouter.ASSET_LIST_COLUMNS,
                object_type="Asset",
                builtin_views=AssetRouter.ASSET_LIST_BUILTINS,
            )
            pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
            return {"views": views, "pinned_view_id": pinned_view_id}
        except Exception as e:
            logger.error(f"Error listing asset views: {str(e)}")
            return {"views": [], "pinned_view_id": None}

    @staticmethod
    @router.post("/views")
    @handle_agent_errors
    async def create_asset_view(payload: dict = Body(...), db: Session = Depends(get_db)):
        try:
            view = LeadListViewService.create_view(
                db,
                payload,
                AssetRouter.ASSET_LIST_COLUMNS,
                object_type="Asset",
                builtin_views=AssetRouter.ASSET_LIST_BUILTINS,
            )
            return JSONResponse(content={"status": "success", "view": view})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error creating asset view: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.put("/views/{view_id}")
    @handle_agent_errors
    async def update_asset_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
        try:
            view = LeadListViewService.update_view(
                db,
                view_id,
                payload,
                AssetRouter.ASSET_LIST_COLUMNS,
                object_type="Asset",
                builtin_views=AssetRouter.ASSET_LIST_BUILTINS,
            )
            return JSONResponse(content={"status": "success", "view": view})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error updating asset view {view_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.delete("/views/{view_id}")
    @handle_agent_errors
    async def delete_asset_view(view_id: str, db: Session = Depends(get_db)):
        try:
            LeadListViewService.delete_view(db, view_id, object_type="Asset")
            return JSONResponse(content={"status": "success"})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error deleting asset view {view_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.post("/views/{view_id}/pin")
    @handle_agent_errors
    async def pin_asset_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
        try:
            payload = payload or {}
            pinned_view_id = LeadListViewService.set_pinned_view(
                db,
                view_id,
                AssetRouter.ASSET_LIST_COLUMNS,
                pinned=bool(payload.get("pinned", True)),
                object_type="Asset",
                builtin_views=AssetRouter.ASSET_LIST_BUILTINS,
            )
            return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})
        except Exception as e:
            logger.error(f"Error pinning asset view {view_id}: {str(e)}")
            return JSONResponse(status_code=500, content={"status": "error", "message": "Internal server error"})

    @staticmethod
    @router.get("/new", response_class=HTMLResponse)
    @handle_agent_errors
    async def new_asset_form(request: Request, contact_id: str = None, db: Session = Depends(get_db)):
        if not is_feature_enabled("assets"):
            return RedirectResponse(url="/?error=Coming+Soon")
        
        return templates.TemplateResponse(request, "asset/create_edit_modal.html", {
            "request": request,
            "object_type": "Asset",
            "is_new": True,
            "contact_id": contact_id
        })

    @staticmethod
    @router.get("/{asset_id}", response_class=HTMLResponse)
    @handle_agent_errors
    async def asset_detail(request: Request, asset_id: str, db: Session = Depends(get_db)):
        if not is_feature_enabled("assets"):
            return RedirectResponse(url="/?error=Coming+Soon")
        try:
            logger.info(f"Accessing Asset Detail: {asset_id}")
            asset = AssetService.get_asset(db, asset_id)
            if not asset: return RedirectResponse(url="/assets?error=Asset+not+found")
            
            contact = ContactService.get_contact(db, asset.contact) if asset.contact else None
            prod = ProductService.get_product(db, asset.product) if asset.product else None
            model = ModelService.get_model(db, asset.model) if asset.model else None
            brand = BrandService.get_vehicle_spec(db, asset.brand) if asset.brand else (BrandService.get_vehicle_spec(db, model.brand) if (model and model.brand) else None)
            
            details = {
                "Name": asset.name if asset.name else "",
                "VIN": asset.vin if asset.vin else "",
                "Status": asset.status if asset.status else "",
                "Price": asset.price if asset.price else 0,
                "Contact": AssetRouter._contact_display_name(contact),
                "Contact_Hidden_Ref": asset.contact if asset.contact else "",
                "Brand": brand.name if brand else "",
                "Brand_Hidden_Ref": brand.id if brand else "",
                "Model": model.name if model else "",
                "Model_Hidden_Ref": asset.model if asset.model else "",
                "Product": prod.name if prod else "",
                "Product_Hidden_Ref": asset.product if asset.product else ""
            }

            related_lists = []
            if contact:
                related_lists.append({
                    "title": "Contact",
                    "icon": "contact",
                    "columns": ["Name", "Email", "Phone"],
                    "view_all_url": f"/contacts?id={contact.id}&related=1&back_to=/assets/{asset_id}?tab=related",
                    "total_count": 1,
                    "items": [{
                        "name": AssetRouter._contact_display_name(contact),
                        "email": contact.email or "",
                        "phone": contact.phone or "",
                        "_href": f"/contacts/{contact.id}",
                    }],
                })

            if prod:
                related_lists.append({
                    "title": "Product",
                    "icon": "product",
                    "columns": ["Name", "Category", "Price"],
                    "view_all_url": f"/products?id={prod.id}&related=1&back_to=/assets/{asset_id}?tab=related",
                    "total_count": 1,
                    "items": [{
                        "name": prod.name or "",
                        "category": prod.category or "",
                        "price": f"{prod.base_price:,}" if prod.base_price else "0",
                        "_href": f"/products/{prod.id}",
                    }],
                })

            if model:
                related_lists.append({
                    "title": "Model",
                    "icon": "model",
                    "columns": ["Name", "Description"],
                    "view_all_url": f"/models?id={model.id}&related=1&back_to=/assets/{asset_id}?tab=related",
                    "total_count": 1,
                    "items": [{
                        "name": model.name or "",
                        "description": model.description or "",
                        "_href": f"/models/{model.id}",
                    }],
                })

            if brand:
                related_lists.append({
                    "title": "Brand",
                    "icon": "brand",
                    "columns": ["Name", "Type"],
                    "view_all_url": f"/vehicle_specifications?id={brand.id}&related=1&back_to=/assets/{asset_id}?tab=related",
                    "total_count": 1,
                    "items": [{
                        "name": brand.name or "",
                        "type": brand.record_type or "",
                        "_href": f"/vehicle_specifications/{brand.id}",
                    }],
                })

            return templates.TemplateResponse(request, "asset/detail_view.html", {
                "request": request, "object_type": "Asset", "plural_type": "assets",
                "record_id": asset_id, "record_name": asset.name if asset.name else "",
                "details": details, "created_at": asset.created_at, "updated_at": asset.updated_at,
                "related_lists": related_lists
            })
        except Exception as e:
            logger.error(f"Error rendering asset detail {asset_id}: {str(e)}")
            return RedirectResponse(url="/assets?error=Internal+server+error")

    @staticmethod
    @router.get("/", response_class=HTMLResponse)
    @handle_agent_errors
    async def list_assets(request: Request, db: Session = Depends(get_db)):
        if not is_feature_enabled("assets"):
            return RedirectResponse(url="/?error=Coming+Soon")
        try:
            related_mode = request.query_params.get("related") == "1" or bool(request.query_params.get("back_to"))
            back_url = request.query_params.get("back_to") or "/assets"
            filters = {"deleted_at": None}
            record_id = request.query_params.get("id")
            if record_id:
                filters["id"] = record_id
                related_mode = True
            for key in ["contact", "product", "brand", "model"]:
                value = request.query_params.get(key)
                if value:
                    filters[key] = value
                    related_mode = True
            
            assets = db.query(Asset).filter_by(**filters).all() if len(filters) > 1 else AssetService.get_assets(db)
            items = []
            for a in assets:
                items.append({
                    "id": a.id,
                    "name": a.name if a.name else "",
                    "vin": a.vin if a.vin else "",
                    "price": a.price if a.price else 0,
                    "status": a.status if a.status else "",
                    "edit_url": f"/assets/new-modal?id={a.id}",
                    "_href": f"/assets/{a.id}"
                })
            
            if related_mode:
                new_query = []
                for key in ["contact", "product", "brand", "model"]:
                    value = request.query_params.get(key)
                    if value:
                        new_query.append(f"{key}={value}")
                new_url = "/assets/new-modal"
                if new_query:
                    new_url += "?" + "&".join(new_query)
                return templates.TemplateResponse(request, "related/list_view.html", {
                    "request": request,
                    "page_title": "Assets",
                    "items": items,
                    "columns": AssetRouter.ASSET_LIST_COLUMNS,
                    "back_url": back_url,
                    "new_url": new_url,
                    "page_icon": "asset",
                    "show_actions": True,
                })
            
            saved_views = LeadListViewService.list_views(
                db,
                AssetRouter.ASSET_LIST_COLUMNS,
                object_type="Asset",
                builtin_views=AssetRouter.ASSET_LIST_BUILTINS,
            )
            saved_view_ids = {view["id"] for view in saved_views}
            pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
            requested_view = request.query_params.get("view")
            current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "asset-all")
            
            return templates.TemplateResponse(request, "asset/list_view.html", {
                "request": request, 
                "object_type": "Asset", 
                "plural_type": "assets",
                "items": items, 
                "columns": AssetRouter.ASSET_LIST_COLUMNS,
                "current_view": current_view,
                "list_view_options": [{"value": view["id"], "label": view["label"]} for view in saved_views],
                "saved_views": saved_views,
                "pinned_view_id": pinned_view_id,
                "list_view_storage_key": "d4_recent_assets",
            })
        except Exception as e:
            logger.error(f"Error listing assets: {str(e)}")
            return RedirectResponse(url="/?error=Internal+server+error")

    @staticmethod
    @router.post("/")
    @handle_agent_errors
    async def create_asset(
        name: Optional[str] = Form(None),
        contact: Optional[str] = Form(None),
        product: Optional[str] = Form(None),
        brand: Optional[str] = Form(None),
        model: Optional[str] = Form(None),
        vin: Optional[str] = Form(None),
        price: Optional[int] = Form(None),
        status: Optional[str] = Form(None),
        db: Session = Depends(get_db)
    ):
        try:
            asset = AssetService.create_asset(
                db, name=name, contact=contact, product=product, 
                brand=brand, model=model, vin=vin, price=price, status=status
            )
            return RedirectResponse(url=f"/assets/{asset.id}?success=Record+created+successfully", status_code=303)
        except Exception as e:
            logger.error(f"Error creating asset: {str(e)}")
            return RedirectResponse(url="/assets?error=Failed+to+create+record", status_code=303)

    @staticmethod
    @router.post("/{asset_id}")
    @handle_agent_errors
    async def update_asset(
        asset_id: str,
        name: Optional[str] = Form(None),
        contact: Optional[str] = Form(None),
        product: Optional[str] = Form(None),
        brand: Optional[str] = Form(None),
        model: Optional[str] = Form(None),
        contact_id: Optional[str] = Form(None),
        product_id: Optional[str] = Form(None),
        brand_id: Optional[str] = Form(None),
        model_id: Optional[str] = Form(None),
        vin: Optional[str] = Form(None),
        price: Optional[int] = Form(None),
        status: Optional[str] = Form(None),
        db: Session = Depends(get_db)
    ):
        try:
            resolved_contact = contact if contact is not None else contact_id
            resolved_product = product if product is not None else product_id
            resolved_brand = brand if brand is not None else brand_id
            resolved_model = model if model is not None else model_id
            AssetService.update_asset(
                db,
                asset_id,
                name=name,
                contact=resolved_contact,
                product=resolved_product,
                brand=resolved_brand,
                model=resolved_model,
                vin=vin,
                price=price,
                status=status,
            )
            return RedirectResponse(url=f"/assets/{asset_id}?success=Record+updated+successfully", status_code=303)
        except Exception as e:
            logger.error(f"Error updating asset {asset_id}: {str(e)}")
            return RedirectResponse(url=f"/assets/{asset_id}?error=Failed+to+update+record", status_code=303)

    @staticmethod
    @router.post("/{asset_id}/delete")
    @handle_agent_errors
    async def delete_asset(request: Request, asset_id: str, db: Session = Depends(get_db)):
        try:
            AssetService.delete_asset(db, asset_id)
            if "application/json" in request.headers.get("Accept", ""):
                return {"status": "success", "message": "Record deleted successfully"}
            return RedirectResponse(url="/assets?success=Record+deleted+successfully", status_code=303)
        except Exception as e:
            logger.error(f"Error deleting asset {asset_id}: {str(e)}")
            return RedirectResponse(url="/assets?error=Failed+to+delete+record", status_code=303)
