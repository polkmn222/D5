from typing import Optional

from fastapi import APIRouter, Request, Depends, Form, Body
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Asset
from web.backend.app.services.asset_service import AssetService
from web.backend.app.utils.error_handler import handle_agent_errors
from web.backend.app.services.lead_list_view_service import LeadListViewService
from web.backend.app.services.contact_service import ContactService
from web.backend.app.services.product_service import ProductService
from web.backend.app.services.model_service import ModelService
from web.backend.app.services.vehicle_spec_service import VehicleSpecService as BrandService
from web.backend.app.core.templates import templates
import logging

from web.backend.app.core.toggles import is_feature_enabled

router = APIRouter()
logger = logging.getLogger(__name__)
ASSET_LIST_COLUMNS = ["name", "vin", "price", "status"]
ASSET_LIST_BUILTINS = (
    {"id": "asset-all", "label": "All Assets", "source": "all"},
    {"id": "asset-recent", "label": "Recently Viewed", "source": "recent"},
)


@router.get("/views")
@handle_agent_errors
async def list_asset_views(db: Session = Depends(get_db)):
    views = LeadListViewService.list_views(
        db,
        ASSET_LIST_COLUMNS,
        object_type="Asset",
        builtin_views=ASSET_LIST_BUILTINS,
    )
    pinned_view_id = next((view["id"] for view in views if view.get("isPinned")), None)
    return {"views": views, "pinned_view_id": pinned_view_id}


@router.post("/views")
@handle_agent_errors
async def create_asset_view(payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.create_view(
            db,
            payload,
            ASSET_LIST_COLUMNS,
            object_type="Asset",
            builtin_views=ASSET_LIST_BUILTINS,
        )
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.put("/views/{view_id}")
@handle_agent_errors
async def update_asset_view(view_id: str, payload: dict = Body(...), db: Session = Depends(get_db)):
    try:
        view = LeadListViewService.update_view(
            db,
            view_id,
            payload,
            ASSET_LIST_COLUMNS,
            object_type="Asset",
            builtin_views=ASSET_LIST_BUILTINS,
        )
        return JSONResponse(content={"status": "success", "view": view})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.delete("/views/{view_id}")
@handle_agent_errors
async def delete_asset_view(view_id: str, db: Session = Depends(get_db)):
    try:
        LeadListViewService.delete_view(db, view_id, object_type="Asset")
        return JSONResponse(content={"status": "success"})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})


@router.post("/views/{view_id}/pin")
@handle_agent_errors
async def pin_asset_view(view_id: str, payload: dict = Body(default=None), db: Session = Depends(get_db)):
    payload = payload or {}
    try:
        pinned_view_id = LeadListViewService.set_pinned_view(
            db,
            view_id,
            ASSET_LIST_COLUMNS,
            pinned=bool(payload.get("pinned", True)),
            object_type="Asset",
            builtin_views=ASSET_LIST_BUILTINS,
        )
        return JSONResponse(content={"status": "success", "pinned_view_id": pinned_view_id})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(exc)})

@router.get("/new", response_class=HTMLResponse)
@handle_agent_errors
async def new_asset_form(request: Request, contact_id: str = None, db: Session = Depends(get_db)):
    if not is_feature_enabled("assets"):
        return RedirectResponse(url="/?error=Coming+Soon")
    
    return templates.TemplateResponse(request, "assets/create_edit_modal.html", {
        "request": request,
        "object_type": "Asset",
        "is_new": True,
        "contact_id": contact_id
    })

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
            "Contact": f"{contact.first_name} {contact.last_name}" if contact else (contact.name if contact else ""),
            "Contact_Hidden_Ref": asset.contact if asset.contact else "",
            "Brand": brand.name if brand else "",
            "Brand_Hidden_Ref": brand.id if brand else "",
            "Model": model.name if model else "",
            "Model_Hidden_Ref": asset.model if asset.model else "",
            "Product": prod.name if prod else "",
            "Product_Hidden_Ref": asset.product if asset.product else ""
        }
        return templates.TemplateResponse(request, "assets/detail_view.html", {
            "request": request, "object_type": "Asset", "plural_type": "assets",
            "record_id": asset_id, "record_name": asset.name if asset.name else "",
            "details": details, "created_at": asset.created_at, "updated_at": asset.updated_at,
            "related_lists": []
        })
    except Exception as e:
        logger.error(f"Error loading asset detail: {e}")
        return RedirectResponse(url=f"/assets?error=Error+loading+asset+detail:+{str(e).replace(' ', '+')}")

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
            return templates.TemplateResponse(request, "related/list_view.html", {
                "request": request,
                "page_title": "Assets",
                "items": items,
                "columns": ASSET_LIST_COLUMNS,
                "back_url": back_url,
                "new_url": None,
                "show_actions": True,
            })
        saved_views = LeadListViewService.list_views(
            db,
            ASSET_LIST_COLUMNS,
            object_type="Asset",
            builtin_views=ASSET_LIST_BUILTINS,
        )
        saved_view_ids = {view["id"] for view in saved_views}
        pinned_view_id = next((view["id"] for view in saved_views if view.get("isPinned")), None)
        requested_view = request.query_params.get("view")
        current_view = requested_view if requested_view in saved_view_ids else (pinned_view_id or "asset-all")
        return templates.TemplateResponse(request, "assets/list_view.html", {
            "request": request, 
            "object_type": "Asset", 
            "plural_type": "assets",
            "items": items, 
            "columns": ASSET_LIST_COLUMNS,
            "current_view": current_view,
            "list_view_options": [{"value": view["id"], "label": view["label"]} for view in saved_views],
            "saved_views": saved_views,
            "pinned_view_id": pinned_view_id,
            "list_view_storage_key": "d4_recent_assets",
        })
    except Exception as e:
        logger.error(f"Error listing assets: {e}")
        return RedirectResponse(url="/?error=Error+loading+assets")

@router.post("/{asset_id}")
async def update_asset_endpoint(
    asset_id: str,
    name: Optional[str] = Form(None),
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
        AssetService.update_asset(
            db, asset_id, name=name, contact_id=contact_id, product_id=product_id, 
            brand_id=brand_id, model_id=model_id, vin=vin, price=price, status=status
        )
        return RedirectResponse(url=f"/assets/{asset_id}?success=Record+updated+successfully", status_code=303)
    except Exception as e:
        logger.error(f"Error updating asset: {e}")
        return RedirectResponse(url=f"/assets/{asset_id}?error=Error+updating+record:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/{asset_id}/delete")
async def delete_asset(request: Request, asset_id: str, db: Session = Depends(get_db)):
    try:
        AssetService.delete_asset(db, asset_id)
        if request.headers.get("Accept") == "application/json":
            return {"status": "success", "message": "Record deleted"}
        return RedirectResponse(url="/assets?success=Deleted", status_code=303)
    except Exception as e:
        logger.error(f"Delete Asset error: {e}")
        return RedirectResponse(url=f"/assets?error=Error+deleting+asset:+{str(e).replace(' ', '+')}", status_code=303)

@router.post("/")
async def create_asset_endpoint(
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
        logger.error(f"Error creating asset: {e}")
        return RedirectResponse(url=f"/assets?error=Error+creating+record:+{str(e).replace(' ', '+')}", status_code=303)
