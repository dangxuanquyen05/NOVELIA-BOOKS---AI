"""Pydantic schemas for Phase 8 Logistics & Shipping Integration."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ShipmentDispatchCreateRequest(BaseModel):
    """Staff payload to dispatch an order through a carrier."""

    carrier: str = Field("GHN", description="Carrier code: GHN, GHTK, or MOCK")
    weight: int = Field(500, ge=10, le=50000, description="Weight in grams")
    length: int = Field(20, ge=1, le=200, description="Length in cm")
    width: int = Field(15, ge=1, le=200, description="Width in cm")
    height: int = Field(5, ge=1, le=200, description="Height in cm")
    required_note: str = Field(
        "CHOXEMHANGKHONGTHU",
        description="Delivery note: CHOXEMHANGKHONGTHU, CHOTHUHANG, or KHONGCHOXEMHANG",
    )
    staff_notes: Optional[str] = Field(None, max_length=255)


class ShipmentEventResponse(BaseModel):
    """Logistics checkpoint event."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    description: str
    location: Optional[str] = None
    occurred_at: datetime


class ShipmentDetailResponse(BaseModel):
    """Detailed shipment and carrier tracking view."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    order_code: str
    carrier: str
    tracking_code: Optional[str] = None
    status: str
    status_label: str
    shipping_fee: Decimal
    estimated_delivery_date: Optional[date] = None
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    recipient_name: str
    recipient_phone: str
    shipping_address: str
    events: List[ShipmentEventResponse] = []
    created_at: datetime


class ShipmentTrackingLookupResponse(BaseModel):
    """Public or customer tracking summary."""

    model_config = ConfigDict(from_attributes=True)

    tracking_code: str
    order_code: str
    carrier: str
    status: str
    status_label: str
    estimated_delivery_date: Optional[date] = None
    delivered_at: Optional[datetime] = None
    events: List[ShipmentEventResponse] = []


class ShippingProviderStatusResponse(BaseModel):
    """Carrier readiness and configuration diagnostics."""

    carrier: str
    environment: str
    is_live_ready: bool
    status_text: str
    api_url: str
    notes: str
