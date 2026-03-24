from fastapi import APIRouter
import logging

# Shared Core Routers
from web.backend.app.api import form_router
from web.backend.app.api.routers import dashboard_router
from web.backend.app.api.routers import utility_router
from web.backend.app.api.routers import bulk_router

# Modular Object Routers
from web.objects.lead.backend.router import LeadRouter
from web.objects.contact.backend.router import ContactRouter
from web.objects.opportunity.backend.router import OpportunityRouter
from web.objects.asset.backend.router import AssetRouter
from web.objects.product.backend.router import ProductRouter
from web.objects.vehicle_spec.backend.router import VehicleSpecRouter

# Feature Routers (Messaging)
from web.message.backend.routers import message_router
from web.message.backend.routers import message_template_router
from web.message.backend import router as messaging_router

logger = logging.getLogger(__name__)

api_router = APIRouter()

# Core
api_router.include_router(dashboard_router.router)
api_router.include_router(form_router.router)

# Objects
api_router.include_router(LeadRouter.router, prefix="/leads", tags=["Leads"])
api_router.include_router(ContactRouter.router, prefix="/contacts", tags=["Contacts"])
api_router.include_router(OpportunityRouter.router, prefix="/opportunities", tags=["Opportunities"])
api_router.include_router(AssetRouter.router, prefix="/assets", tags=["Assets"])
api_router.include_router(ProductRouter.router, prefix="/products", tags=["Products"])
api_router.include_router(VehicleSpecRouter.router, tags=["Vehicle Specifications"])

# Features
api_router.include_router(message_router.router, prefix="/messages", tags=["Messages"])
api_router.include_router(message_template_router.router, prefix="/message_templates", tags=["Message Templates"])
api_router.include_router(utility_router.router)
api_router.include_router(bulk_router.router)
api_router.include_router(messaging_router.router)
