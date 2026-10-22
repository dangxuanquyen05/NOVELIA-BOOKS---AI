"""Repository for shopping cart, cart items, wishlist, and wishlist items."""

from typing import Optional
from sqlalchemy.orm import Session, selectinload

from app.models.catalog import Book
from app.models.commerce import Cart, CartItem, Wishlist, WishlistItem
from app.models.inventory import Inventory


class CartRepository:
    """Data access layer for user-isolated shopping carts in MySQL."""

    @staticmethod
    def _eager_load_options():
        return [
            selectinload(Cart.items)
            .selectinload(CartItem.book)
            .selectinload(Book.inventory),
        ]

    @classmethod
    def get_or_create_cart(cls, db: Session, user_id: int) -> Cart:
        """Retrieve existing user cart or initialize a fresh one."""
        cart = (
            db.query(Cart)
            .options(*cls._eager_load_options())
            .filter(Cart.user_id == user_id)
            .first()
        )
        if not cart:
            cart = Cart(user_id=user_id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
            # Re-query with eager loading
            cart = (
                db.query(Cart)
                .options(*cls._eager_load_options())
                .filter(Cart.id == cart.id)
                .first()
            )
        return cart

    # Convenience alias
    get_or_create = get_or_create_cart

    @staticmethod
    def get_cart_item(
        db: Session, cart_id: int, book_id: int
    ) -> Optional[CartItem]:
        return (
            db.query(CartItem)
            .filter(CartItem.cart_id == cart_id, CartItem.book_id == book_id)
            .first()
        )

    @classmethod
    def add_item(
        cls, db: Session, cart_id: int, book_id: int, quantity: int
    ) -> CartItem:
        """Add item or increment quantity if already present."""
        item = cls.get_cart_item(db, cart_id, book_id)
        if item:
            item.quantity += quantity
        else:
            item = CartItem(cart_id=cart_id, book_id=book_id, quantity=quantity)
            db.add(item)
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def update_item_quantity(
        cls, db: Session, cart_id: int, book_id: int, quantity: int
    ) -> Optional[CartItem]:
        item = cls.get_cart_item(db, cart_id, book_id)
        if item:
            item.quantity = quantity
            db.commit()
            db.refresh(item)
        return item

    @classmethod
    def remove_item(cls, db: Session, cart_id: int, book_id: int) -> bool:
        item = cls.get_cart_item(db, cart_id, book_id)
        if item:
            db.delete(item)
            db.commit()
            return True
        return False

    @staticmethod
    def clear_cart(db: Session, cart_id: int) -> None:
        db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
        db.commit()


class WishlistRepository:
    """Data access layer for customer wishlists."""

    @staticmethod
    def _eager_load_options():
        return [
            selectinload(Wishlist.items)
            .selectinload(WishlistItem.book)
            .selectinload(Book.inventory),
        ]

    @classmethod
    def get_or_create_wishlist(cls, db: Session, user_id: int) -> Wishlist:
        wishlist = (
            db.query(Wishlist)
            .options(*cls._eager_load_options())
            .filter(Wishlist.user_id == user_id)
            .first()
        )
        if not wishlist:
            wishlist = Wishlist(user_id=user_id, name="Sách Yêu Thích")
            db.add(wishlist)
            db.commit()
            db.refresh(wishlist)
            wishlist = (
                db.query(Wishlist)
                .options(*cls._eager_load_options())
                .filter(Wishlist.id == wishlist.id)
                .first()
            )
        return wishlist

    @staticmethod
    def get_item(
        db: Session, wishlist_id: int, book_id: int
    ) -> Optional[WishlistItem]:
        return (
            db.query(WishlistItem)
            .filter(
                WishlistItem.wishlist_id == wishlist_id,
                WishlistItem.book_id == book_id,
            )
            .first()
        )

    @classmethod
    def add_item(
        cls, db: Session, wishlist_id: int, book_id: int
    ) -> WishlistItem:
        item = cls.get_item(db, wishlist_id, book_id)
        if not item:
            item = WishlistItem(wishlist_id=wishlist_id, book_id=book_id)
            db.add(item)
            db.commit()
            db.refresh(item)
        return item

    @classmethod
    def remove_item(cls, db: Session, wishlist_id: int, book_id: int) -> bool:
        item = cls.get_item(db, wishlist_id, book_id)
        if item:
            db.delete(item)
            db.commit()
            return True
        return False
