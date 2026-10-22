"""Database models registry for NOVELIA BOOKS.
Aggregates all SQLAlchemy models for clean imports and Alembic autogenerate discovery.
"""

from app.database.connection import Base

# A. Users & Access
from app.models.user import (
    Role,
    User,
    UserAddress,
    UserPreference,
    UserRole,
)

# B. Catalog
from app.models.catalog import (
    Author,
    Book,
    BookAuthor,
    BookCategory,
    BookImage,
    Category,
    Publisher,
)

# C. Inventory
from app.models.inventory import (
    Inventory,
    InventoryTransaction,
)

# D. Commerce
from app.models.commerce import (
    Cart,
    CartItem,
    Coupon,
    CouponUsage,
    Order,
    OrderItem,
    Wishlist,
    WishlistItem,
)

# E. Payment & Shipping
from app.models.payment_shipping import (
    Payment,
    RefundRequest,
    Shipment,
    ShipmentEvent,
)

# F. Customer Experience
from app.models.experience import (
    Notification,
    Review,
)

# G. AI Ecosystem
from app.models.ai import (
    AIActionLog,
    AIConversation,
    AIMessage,
    BookRecommendation,
    UserBookEvent,
)

# H. System & Audit
from app.models.audit import (
    AuditLog,
)

__all__ = [
    "Base",
    # Users & Access
    "Role",
    "User",
    "UserAddress",
    "UserPreference",
    "UserRole",
    # Catalog
    "Author",
    "Book",
    "BookAuthor",
    "BookCategory",
    "BookImage",
    "Category",
    "Publisher",
    # Inventory
    "Inventory",
    "InventoryTransaction",
    # Commerce
    "Cart",
    "CartItem",
    "Coupon",
    "CouponUsage",
    "Order",
    "OrderItem",
    "Wishlist",
    "WishlistItem",
    # Payment & Shipping
    "Payment",
    "RefundRequest",
    "Shipment",
    "ShipmentEvent",
    # Experience
    "Notification",
    "Review",
    # AI Ecosystem
    "AIActionLog",
    "AIConversation",
    "AIMessage",
    "BookRecommendation",
    "UserBookEvent",
    # Audit
    "AuditLog",
]
