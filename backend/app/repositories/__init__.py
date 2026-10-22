"""Repositories package registry."""

from app.repositories.user_repo import UserRepository
from app.repositories.catalog_repo import (
    AuthorRepository,
    BookRepository,
    CategoryRepository,
    PublisherRepository,
)
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.commerce_repo import CartRepository, WishlistRepository
from app.repositories.review_repo import ReviewRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.coupon_repo import CouponRepository
from app.repositories.admin_dashboard_repo import AdminDashboardRepository
from app.repositories.shipment_repo import ShipmentRepository
from app.repositories.recommendation_repo import RecommendationRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.audit_repo import AuditRepository

__all__ = [
    "UserRepository",
    "AuthorRepository",
    "BookRepository",
    "CategoryRepository",
    "PublisherRepository",
    "InventoryRepository",
    "CartRepository",
    "WishlistRepository",
    "ReviewRepository",
    "OrderRepository",
    "CouponRepository",
    "AdminDashboardRepository",
    "ShipmentRepository",
    "RecommendationRepository",
    "NotificationRepository",
    "AuditRepository",
]



