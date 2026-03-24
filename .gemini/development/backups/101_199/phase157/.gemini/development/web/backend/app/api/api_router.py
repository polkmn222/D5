from fastapi import APIRouter
from .routers import dashboard_router
from . import form_router
from web.backend.app.api.routers import lead_router
from web.backend.app.api.routers import contact_router
from web.backend.app.api.routers import opportunity_router
from web.backend.app.api.routers import asset_router
from web.backend.app.api.routers import product_router
from web.backend.app.api.routers import vehicle_spec_router
from web.backend.app.api.routers import utility_router
from web.backend.app.api.routers import bulk_router

# Feature Routers
from web.message.backend.routers import message_router
from web.message.backend.routers import message_template_router
from web.message.backend import router as messaging_router

api_router = APIRouter()

# Dashboard
api_router.include_router(dashboard_router.router)
api_router.include_router(form_router.router)

# Objects
api_router.include_router(lead_router.router, prefix="/leads", tags=["Leads"])
api_router.include_router(contact_router.router, prefix="/contacts", tags=["Contacts"])
api_router.include_router(opportunity_router.router, prefix="/opportunities", tags=["Opportunities"])
api_router.include_router(asset_router.router, prefix="/assets", tags=["Assets"])
api_router.include_router(product_router.router, prefix="/products", tags=["Products"])
api_router.include_router(vehicle_spec_router.router, tags=["Vehicle Specifications"])

# Messaging
api_router.include_router(message_router.router, prefix="/messages", tags=["Messages"])
api_router.include_router(message_template_router.router, prefix="/message_templates", tags=["Message Templates"])
api_router.include_router(utility_router.router)
api_router.include_router(bulk_router.router)
api_router.include_router(messaging_router.router)
