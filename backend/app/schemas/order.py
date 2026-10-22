"""Schemas for checkout, order placement, order lifecycle, and coupon validation."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class OrderItemRead(BaseModel):
    """Snapshot metadata of an ordered book at purchase time."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: Optional[int] = None
    book_title_snapshot: str
    book_isbn_snapshot: str
    book_sku_snapshot: str
    price_at_purchase: Decimal
    quantity: int
    subtotal: Decimal
    created_at: datetime


class OrderRead(BaseModel):
    """Full customer order representation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_code: str
    user_id: int
    subtotal_amount: Decimal
    shipping_fee: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    status: str
    
    # Delivery snapshot
    recipient_name: str
    recipient_phone: str
    shipping_province: str
    shipping_district: str
    shipping_ward: str
    shipping_street_address: str
    shipping_formatted_address: Optional[str] = None
    shipping_latitude: Optional[float] = None
    shipping_longitude: Optional[float] = None
    customer_notes: Optional[str] = None
    staff_notes: Optional[str] = None
    cancelled_reason: Optional[str] = None
    
    # Payment info
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    payment_url: Optional[str] = None  # Redirect URL for gateway sandbox

    # Shipment info
    shipment_carrier: Optional[str] = None
    shipment_tracking_code: Optional[str] = None
    shipment_status: Optional[str] = None
    
    items: List[OrderItemRead] = []
    created_at: datetime
    updated_at: datetime


class CheckoutRequest(BaseModel):
    """Customer checkout submission. Backend recalculates prices and stock authoritatively."""

    recipient_name: str = Field(..., min_length=2, max_length=100)
    recipient_phone: str = Field(..., min_length=9, max_length=20)
    shipping_province: str = Field(..., min_length=2, max_length=100)
    shipping_district: str = Field(..., min_length=2, max_length=100)
    shipping_ward: str = Field(..., min_length=2, max_length=100)
    shipping_street_address: str = Field(..., min_length=5, max_length=255)
    shipping_formatted_address: Optional[str] = Field(None, max_length=500)
    shipping_latitude: Optional[float] = None
    shipping_longitude: Optional[float] = None
    customer_notes: Optional[str] = Field(None, max_length=500)
    coupon_code: Optional[str] = Field(None, max_length=50)
    payment_method: str = Field("COD", description="COD, VNPAY, MOMO, BANK_TRANSFER")
    idempotency_key: Optional[str] = Field(None, max_length=100, description="Unique client key preventing double submit")


class OrderCancelRequest(BaseModel):
    """Request payload for order cancellation."""

    reason: str = Field(..., min_length=5, max_length=255, description="Bắt buộc có lý do hủy đơn")


class OrderStatusUpdateRequest(BaseModel):
    """Staff/Admin status transition request."""

    status: str = Field(..., description="PENDING, CONFIRMED, PROCESSING, SHIPPING, COMPLETED, CANCELLED")
    staff_notes: Optional[str] = Field(None, max_length=500)
    cancellation_reason: Optional[str] = Field(None, max_length=255)


class CouponValidateRequest(BaseModel):
    """Coupon validation check before checkout."""

    code: str = Field(..., min_length=2, max_length=50)
    cart_subtotal: Optional[Decimal] = Field(None, ge=0)


class CouponValidationResult(BaseModel):
    """Result of coupon code evaluation."""

    is_valid: bool
    code: str
    discount_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    discount_amount: Decimal = Decimal("0.00")
    min_order_value: Optional[Decimal] = None
    message: str


class CouponRead(BaseModel):
    """Public promotional voucher metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    min_order_value: Decimal
    max_discount_value: Optional[Decimal] = None
    start_date: datetime
    end_date: datetime
    is_active: bool


class PaginatedOrdersResponse(BaseModel):
    """Paginated list of orders."""

    items: List[OrderRead]
    total: int
    page: int
    page_size: int
    total_pages: int
