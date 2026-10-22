"""Service layer for shopping cart and wishlist operations with backend pricing and stock enforcement."""

from decimal import Decimal
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.catalog import Book
from app.models.commerce import Cart, CartItem, Wishlist, WishlistItem
from app.repositories.commerce_repo import CartRepository, WishlistRepository
from app.schemas.commerce import (
    CartItemRead,
    CartRead,
    WishlistItemRead,
    WishlistRead,
)


def to_cart_item_read(item: CartItem) -> CartItemRead:
    """Format an individual CartItem with verified pricing and available stock."""
    book = item.book
    inv = book.inventory if book else None
    available = inv.available_stock if inv else 0
    is_avail = (available >= item.quantity) and (book.status == "ACTIVE" if book else False)

    price = Decimal(str(book.price)) if book else Decimal("0.00")
    orig_price = Decimal(str(book.original_price)) if book else price
    subtotal = price * Decimal(item.quantity)

    discount = 0
    if orig_price > price and orig_price > 0:
        discount = int(round(((float(orig_price) - float(price)) / float(orig_price)) * 100))

    return CartItemRead(
        id=item.id,
        book_id=item.book_id,
        book_title=book.title if book else "Không xác định",
        book_isbn=book.isbn if book else "",
        book_sku=book.sku if book else "",
        cover_image_url=book.cover_image_url if book else "",
        unit_price=price,
        original_price=orig_price,
        discount_percent=discount,
        quantity=item.quantity,
        subtotal=subtotal,
        available_stock=available,
        is_available=is_avail,
    )


def to_cart_read(cart: Cart) -> CartRead:
    """Aggregate cart totals and detect any inventory issues."""
    read_items = [to_cart_item_read(item) for item in (cart.items or [])]
    total_qty = sum(i.quantity for i in read_items)
    subtotal_sum = sum(i.subtotal for i in read_items) if read_items else Decimal("0.00")
    has_issues = any(not i.is_available for i in read_items)

    return CartRead(
        id=cart.id,
        user_id=cart.user_id,
        items=read_items,
        total_items=total_qty,
        subtotal_amount=subtotal_sum,
        has_stock_issues=has_issues,
        updated_at=cart.updated_at,
    )


def to_wishlist_item_read(item: WishlistItem) -> WishlistItemRead:
    book = item.book
    inv = book.inventory if book else None
    available = inv.available_stock if inv else 0
    in_stock = available > 0 and (book.status == "ACTIVE" if book else False)

    return WishlistItemRead(
        id=item.id,
        book_id=item.book_id,
        book_title=book.title if book else "Không xác định",
        book_isbn=book.isbn if book else "",
        book_sku=book.sku if book else "",
        cover_image_url=book.cover_image_url if book else "",
        price=Decimal(str(book.price)) if book else Decimal("0.00"),
        original_price=Decimal(str(book.original_price)) if book else Decimal("0.00"),
        is_in_stock=in_stock,
        available_stock=available,
        added_at=item.added_at,
    )


class CartService:
    """Domain logic for shopping carts. Pricing and inventory are authoritative at backend."""

    @classmethod
    def get_cart(cls, db: Session, user_id: int) -> CartRead:
        cart = CartRepository.get_or_create_cart(db, user_id)
        return to_cart_read(cart)

    @classmethod
    def add_item(
        cls, db: Session, user_id: int, book_id: int, quantity: int
    ) -> CartRead:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số lượng sách thêm vào giỏ phải lớn hơn 0.",
            )

        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tác phẩm yêu cầu không tồn tại trong hệ thống.",
            )

        if book.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tác phẩm này hiện không còn kinh doanh hoặc tạm hết hàng.",
            )

        # Check stock availability
        inv = book.inventory
        available = inv.available_stock if inv else 0
        if available <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tác phẩm này hiện đã hết hàng trong kho.",
            )

        cart = CartRepository.get_or_create_cart(db, user_id)
        existing_item = CartRepository.get_cart_item(db, cart.id, book_id)
        current_qty = existing_item.quantity if existing_item else 0
        new_total_qty = current_qty + quantity

        if new_total_qty > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số lượng yêu cầu ({new_total_qty}) vượt quá số lượng khả dụng trong kho ({available} cuốn).",
            )

        CartRepository.add_item(db, cart.id, book_id, quantity)
        cart = CartRepository.get_or_create_cart(db, user_id)
        return to_cart_read(cart)

    @classmethod
    def update_item_quantity(
        cls, db: Session, user_id: int, book_id: int, quantity: int
    ) -> CartRead:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Số lượng sản phẩm trong giỏ hàng phải lớn hơn 0.",
            )

        cart = CartRepository.get_or_create_cart(db, user_id)
        existing_item = CartRepository.get_cart_item(db, cart.id, book_id)
        if not existing_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sách này không có trong giỏ hàng của bạn.",
            )

        book = existing_item.book
        inv = book.inventory if book else None
        available = inv.available_stock if inv else 0

        if quantity > available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Số lượng cập nhật ({quantity}) vượt quá tồn kho khả dụng ({available} cuốn).",
            )

        CartRepository.update_item_quantity(db, cart.id, book_id, quantity)
        cart = CartRepository.get_or_create_cart(db, user_id)
        return to_cart_read(cart)

    @classmethod
    def remove_item(cls, db: Session, user_id: int, book_id: int) -> CartRead:
        cart = CartRepository.get_or_create_cart(db, user_id)
        CartRepository.remove_item(db, cart.id, book_id)
        cart = CartRepository.get_or_create_cart(db, user_id)
        return to_cart_read(cart)

    @classmethod
    def clear_cart(cls, db: Session, user_id: int) -> CartRead:
        cart = CartRepository.get_or_create_cart(db, user_id)
        CartRepository.clear_cart(db, cart.id)
        cart = CartRepository.get_or_create_cart(db, user_id)
        return to_cart_read(cart)


class WishlistService:
    """Domain logic for customer wishlists."""

    @classmethod
    def get_wishlist(cls, db: Session, user_id: int) -> WishlistRead:
        wishlist = WishlistRepository.get_or_create_wishlist(db, user_id)
        read_items = [to_wishlist_item_read(i) for i in (wishlist.items or [])]
        return WishlistRead(
            id=wishlist.id,
            user_id=wishlist.user_id,
            name=wishlist.name,
            items=read_items,
            total_items=len(read_items),
            created_at=wishlist.created_at,
        )

    @classmethod
    def add_item(cls, db: Session, user_id: int, book_id: int) -> WishlistRead:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tác phẩm yêu cầu không tồn tại.",
            )

        wishlist = WishlistRepository.get_or_create_wishlist(db, user_id)
        WishlistRepository.add_item(db, wishlist.id, book_id)
        return cls.get_wishlist(db, user_id)

    @classmethod
    def remove_item(cls, db: Session, user_id: int, book_id: int) -> WishlistRead:
        wishlist = WishlistRepository.get_or_create_wishlist(db, user_id)
        WishlistRepository.remove_item(db, wishlist.id, book_id)
        return cls.get_wishlist(db, user_id)

    @classmethod
    def move_to_cart(cls, db: Session, user_id: int, book_id: int) -> CartRead:
        """Transfer an item from wishlist to active cart and remove from wishlist."""
        cart_res = CartService.add_item(db, user_id=user_id, book_id=book_id, quantity=1)
        cls.remove_item(db, user_id=user_id, book_id=book_id)
        return cart_res
