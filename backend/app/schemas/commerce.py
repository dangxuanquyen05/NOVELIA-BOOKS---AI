"""Pydantic schemas for Shopping Cart and Wishlist customer operations."""

from datetime import datetime
from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class CartItemAddRequest(BaseModel):
    book_id: int
    quantity: int = Field(1, gt=0, le=50, description="Quantity to add (1-50)")


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(..., gt=0, le=50, description="Updated quantity (must be positive, 1-50)")


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    book_title: str
    book_isbn: str
    book_sku: str
    cover_image_url: str
    unit_price: Decimal
    original_price: Decimal
    discount_percent: int
    quantity: int
    subtotal: Decimal
    available_stock: int
    is_available: bool


class CartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    items: List[CartItemRead] = []
    total_items: int = 0
    subtotal_amount: Decimal = Decimal("0.00")
    has_stock_issues: bool = False
    updated_at: datetime


class WishlistItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    book_title: str
    book_isbn: str
    book_sku: str
    cover_image_url: str
    price: Decimal
    original_price: Decimal
    is_in_stock: bool
    available_stock: int
    added_at: datetime


class WishlistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str = "My Wishlist"
    items: List[WishlistItemRead] = []
    total_items: int = 0
    created_at: datetime
