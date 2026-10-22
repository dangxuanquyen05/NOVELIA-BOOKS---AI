"""Pydantic schemas for Inventory management, transactions, and low-stock alerts."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InventoryTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    inventory_id: int
    transaction_type: str
    quantity_change: int
    balance_after: int
    reference_code: Optional[str] = None
    reason: Optional[str] = None
    staff_user_id: Optional[int] = None
    created_at: datetime


class InventoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    book_title: str
    book_isbn: str
    book_sku: str
    cover_image_url: str
    physical_stock: int
    reserved_stock: int
    available_stock: int
    low_stock_threshold: int
    is_low_stock: bool
    updated_at: datetime


class InventoryInboundRequest(BaseModel):
    book_id: int
    quantity: int = Field(..., gt=0, description="Inbound restock quantity (must be positive)")
    reference_code: str = Field(..., min_length=3, max_length=50, description="Invoice or import receipt code")
    reason: Optional[str] = Field("Nhập kho bổ sung định kỳ", max_length=255)


class InventoryAdjustmentRequest(BaseModel):
    book_id: int
    quantity_change: int = Field(..., description="Quantity delta (positive to add, negative to deduct)")
    reference_code: str = Field(..., min_length=3, max_length=50, description="Audit adjustment code")
    reason: str = Field(..., min_length=5, max_length=255, description="Mandatory explanation for audit trail")


class PaginatedInventoryResponse(BaseModel):
    items: List[InventoryRead]
    total: int
    page: int
    page_size: int
    total_pages: int
    low_stock_count: int = 0
