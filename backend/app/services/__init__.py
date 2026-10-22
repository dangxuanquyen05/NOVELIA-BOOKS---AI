"""Services package registry."""

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.catalog_service import CatalogService
from app.services.inventory_service import InventoryService
from app.services.commerce_service import CartService, WishlistService
from app.services.review_service import ReviewService
from app.services.order_service import OrderService
from app.services.bookmatch_service import BookMatchService
from app.services.notification_service import NotificationService
from app.services.audit_service import AuditService
from app.services.email_service import EmailService

__all__ = [
    "AuthService",
    "UserService",
    "CatalogService",
    "InventoryService",
    "CartService",
    "WishlistService",
    "ReviewService",
    "OrderService",
    "BookMatchService",
    "NotificationService",
    "AuditService",
    "EmailService",
]



