"""Shopping Cart API endpoints strictly isolated to authenticated user sessions."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.commerce import (
    CartItemAddRequest,
    CartItemUpdateRequest,
    CartRead,
)
from app.services.commerce_service import CartService

router = APIRouter(prefix="/cart", tags=["Shopping Cart"])


@router.get(
    "",
    response_model=CartRead,
    summary="Retrieve current user's shopping cart with validated prices and available stock",
)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return CartService.get_cart(db, user_id=current_user.id)


@router.post(
    "/items",
    response_model=CartRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a book to shopping cart with stock check",
)
def add_to_cart(
    data: CartItemAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return CartService.add_item(
        db,
        user_id=current_user.id,
        book_id=data.book_id,
        quantity=data.quantity,
    )


@router.put(
    "/items/{book_id}",
    response_model=CartRead,
    summary="Update item quantity in cart",
)
def update_cart_item(
    book_id: int,
    data: CartItemUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return CartService.update_item_quantity(
        db,
        user_id=current_user.id,
        book_id=book_id,
        quantity=data.quantity,
    )


@router.delete(
    "/items/{book_id}",
    response_model=CartRead,
    summary="Remove a book from shopping cart",
)
def remove_from_cart(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return CartService.remove_item(
        db,
        user_id=current_user.id,
        book_id=book_id,
    )


@router.delete(
    "",
    response_model=CartRead,
    summary="Empty the entire shopping cart",
)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return CartService.clear_cart(db, user_id=current_user.id)
