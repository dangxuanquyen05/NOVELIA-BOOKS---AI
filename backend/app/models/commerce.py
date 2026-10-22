"""Commerce models: Carts, CartItems, Wishlists, WishlistItems, Orders, OrderItems, Coupons, CouponUsages."""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    DECIMAL,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Cart(Base):
    """Shopping cart belonging to a user (or guest session)."""

    __tablename__ = "carts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_carts_user", "user_id"),
    )

    user = relationship("User")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    """Item row inside a shopping cart."""

    __tablename__ = "cart_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    cart_id = Column(BigInteger, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("cart_id", "book_id", name="uq_cart_book"),
        CheckConstraint("quantity > 0", name="chk_cart_item_quantity_positive"),
        Index("idx_cart_items_cart", "cart_id"),
        Index("idx_cart_items_book", "book_id"),
    )

    cart = relationship("Cart", back_populates="items")
    book = relationship("Book")


class Wishlist(Base):
    """User wishlist container."""

    __tablename__ = "wishlists"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), default="My Wishlist", nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_wishlists_user", "user_id"),
    )

    user = relationship("User")
    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan")


class WishlistItem(Base):
    """Specific book saved in a user's wishlist."""

    __tablename__ = "wishlist_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    wishlist_id = Column(BigInteger, ForeignKey("wishlists.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("wishlist_id", "book_id", name="uq_wishlist_book"),
        Index("idx_wishlist_items_wishlist", "wishlist_id"),
        Index("idx_wishlist_items_book", "book_id"),
    )

    wishlist = relationship("Wishlist", back_populates="items")
    book = relationship("Book")


class Order(Base):
    """Customer purchase order containing immutable financial snapshot."""

    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_code = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    # Financial breakdown
    subtotal_amount = Column(DECIMAL(12, 2), nullable=False)
    shipping_fee = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    discount_amount = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    total_amount = Column(DECIMAL(12, 2), nullable=False)
    
    # Order Status Lifecycle: PENDING, CONFIRMED, PROCESSING, SHIPPING, COMPLETED, CANCELLED, REFUNDED
    status = Column(String(30), default="PENDING", nullable=False, index=True)
    
    # Recipient & Delivery Snapshot
    recipient_name = Column(String(100), nullable=False)
    recipient_phone = Column(String(20), nullable=False)
    shipping_province = Column(String(100), nullable=False)
    shipping_district = Column(String(100), nullable=False)
    shipping_ward = Column(String(100), nullable=False)
    shipping_street_address = Column(String(255), nullable=False)
    shipping_formatted_address = Column(String(500), nullable=True)
    shipping_latitude = Column(Float, nullable=True)
    shipping_longitude = Column(Float, nullable=True)
    
    customer_notes = Column(Text, nullable=True)
    staff_notes = Column(Text, nullable=True)
    cancelled_reason = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_orders_user", "user_id"),
        Index("idx_orders_status", "status"),
        Index("idx_orders_created_at", "created_at"),
        CheckConstraint("subtotal_amount >= 0", name="chk_order_subtotal_non_negative"),
        CheckConstraint("shipping_fee >= 0", name="chk_order_shipping_non_negative"),
        CheckConstraint("discount_amount >= 0", name="chk_order_discount_non_negative"),
        CheckConstraint("total_amount >= 0", name="chk_order_total_non_negative"),
    )

    user = relationship("User")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False)
    shipment = relationship("Shipment", back_populates="order", uselist=False)
    coupon_usages = relationship("CouponUsage", back_populates="order")


class OrderItem(Base):
    """Line item in an order. Captures permanent metadata snapshot to guard against future catalog modifications."""

    __tablename__ = "order_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="SET NULL"), nullable=True)
    
    # Metadata snapshot at moment of purchase
    book_title_snapshot = Column(String(255), nullable=False)
    book_isbn_snapshot = Column(String(20), nullable=False)
    book_sku_snapshot = Column(String(50), nullable=False)
    price_at_purchase = Column(DECIMAL(12, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    subtotal = Column(DECIMAL(12, 2), nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_order_items_order", "order_id"),
        Index("idx_order_items_book", "book_id"),
        CheckConstraint("quantity > 0", name="chk_order_item_quantity_positive"),
        CheckConstraint("price_at_purchase >= 0", name="chk_order_item_price_non_negative"),
        CheckConstraint("subtotal >= 0", name="chk_order_item_subtotal_non_negative"),
    )

    order = relationship("Order", back_populates="items")
    book = relationship("Book")


class Coupon(Base):
    """Promotional discount voucher."""

    __tablename__ = "coupons"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    discount_type = Column(String(20), nullable=False)  # PERCENTAGE, FIXED_AMOUNT
    discount_value = Column(DECIMAL(12, 2), nullable=False)
    min_order_value = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    max_discount_value = Column(DECIMAL(12, 2), nullable=True)
    usage_limit = Column(Integer, nullable=True)  # Null = unlimited
    used_count = Column(Integer, default=0, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_coupons_code", "code"),
        Index("idx_coupons_active_dates", "is_active", "start_date", "end_date"),
        CheckConstraint("discount_value > 0", name="chk_coupon_discount_value_positive"),
        CheckConstraint("min_order_value >= 0", name="chk_coupon_min_order_non_negative"),
    )

    usages = relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")


class CouponUsage(Base):
    """Historical record of coupon redemptions."""

    __tablename__ = "coupon_usages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    coupon_id = Column(BigInteger, ForeignKey("coupons.id", ondelete="RESTRICT"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    discount_applied = Column(DECIMAL(12, 2), nullable=False)
    used_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("coupon_id", "order_id", name="uq_coupon_order"),
        Index("idx_coupon_usages_coupon", "coupon_id"),
        Index("idx_coupon_usages_user", "user_id"),
        Index("idx_coupon_usages_order", "order_id"),
    )

    coupon = relationship("Coupon", back_populates="usages")
    user = relationship("User")
    order = relationship("Order", back_populates="coupon_usages")
