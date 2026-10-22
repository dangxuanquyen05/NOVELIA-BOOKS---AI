"""API Version 1 Router aggregation."""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.addresses import router as addresses_router
from app.api.v1.catalog import router as catalog_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.cart import router as cart_router
from app.api.v1.wishlist import router as wishlist_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.orders import router as orders_router
from app.api.v1.coupons import router as coupons_router
from app.api.v1.payments import router as payments_router
from app.api.v1.admin_dashboard import router as admin_dashboard_router
from app.api.v1.shipping import router as shipping_router
from app.api.v1.ai import router as ai_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.audit import router as audit_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, prefix="", tags=["Health & Diagnostics"])
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(addresses_router)
api_v1_router.include_router(catalog_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(cart_router)
api_v1_router.include_router(wishlist_router)
api_v1_router.include_router(reviews_router)
api_v1_router.include_router(orders_router)
api_v1_router.include_router(coupons_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(admin_dashboard_router)
api_v1_router.include_router(shipping_router)
api_v1_router.include_router(ai_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(notifications_router)
api_v1_router.include_router(audit_router)



