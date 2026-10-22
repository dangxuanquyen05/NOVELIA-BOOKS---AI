"""Schemas for payment processing, gateway intents, and webhooks."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class PaymentRead(BaseModel):
    """Payment record read model."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    payment_code: str
    order_id: int
    payment_method: str
    payment_status: str
    amount: Decimal
    transaction_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PaymentWebhookPayload(BaseModel):
    """Generic payment webhook payload for payment notifications."""

    gateway: str
    order_code: str
    amount: Decimal
    transaction_id: str
    is_success: bool
    signature: str
    raw_data: Optional[Dict[str, Any]] = None


class PaymentStatusResponse(BaseModel):
    """Status verification response."""

    order_code: str
    payment_status: str
    payment_method: str
    amount: Decimal
    transaction_id: Optional[str] = None
    paid_at: Optional[datetime] = None
