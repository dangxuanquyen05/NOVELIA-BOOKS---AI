"""Wishlist API endpoints for customer saved books."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.commerce import CartRead, WishlistRead
from app.services.commerce_service import WishlistService

router = APIRouter(prefix="/wishlist", tags=["Customer Wishlist"])


@router.get(
    "",
    response_model=WishlistRead,
    summary="Get user's personal wishlist",
)
def get_wishlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return WishlistService.get_wishlist(db, user_id=current_user.id)


@router.post(
    "/{book_id}",
    response_model=WishlistRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save a book to wishlist",
)
def add_to_wishlist(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return WishlistService.add_item(db, user_id=current_user.id, book_id=book_id)


@router.delete(
    "/{book_id}",
    response_model=WishlistRead,
    summary="Remove a book from wishlist",
)
def remove_from_wishlist(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return WishlistService.remove_item(db, user_id=current_user.id, book_id=book_id)


@router.post(
    "/{book_id}/move-to-cart",
    response_model=CartRead,
    summary="Move saved book from wishlist into active shopping cart",
)
def move_wishlist_to_cart(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return WishlistService.move_to_cart(db, user_id=current_user.id, book_id=book_id)
