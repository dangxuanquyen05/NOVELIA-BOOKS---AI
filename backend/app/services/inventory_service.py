"""Service layer for inventory operations, stock auditing, and low-stock alerts."""

import math
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.catalog import Book
from app.models.inventory import Inventory
from app.models.user import User
from app.repositories.inventory_repo import InventoryRepository
from app.schemas.inventory import (
    InventoryAdjustmentRequest,
    InventoryInboundRequest,
    InventoryRead,
    InventoryTransactionRead,
    PaginatedInventoryResponse,
)


def to_inventory_read(inv: Inventory) -> InventoryRead:
    """Map ORM Inventory to Pydantic InventoryRead schema."""
    book = inv.book
    available = inv.physical_stock - inv.reserved_stock
    is_low = available <= inv.low_stock_threshold

    return InventoryRead(
        id=inv.id,
        book_id=inv.book_id,
        book_title=(book.title if book and book.title else "Không xác định"),
        book_isbn=(book.isbn if book and book.isbn else ""),
        book_sku=(book.sku if book and book.sku else f"NOV-BK-{inv.book_id:04d}"),
        cover_image_url=(book.cover_image_url if book and book.cover_image_url else ""),
        physical_stock=inv.physical_stock,
        reserved_stock=inv.reserved_stock,
        available_stock=available,
        low_stock_threshold=inv.low_stock_threshold,
        is_low_stock=is_low,
        updated_at=inv.updated_at,
    )


class InventoryService:
    """Core domain business logic for stock tracking and transactions."""

    @classmethod
    def get_inventory(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        query: Optional[str] = None,
        low_stock_only: bool = False,
    ) -> PaginatedInventoryResponse:
        items, total, low_count = InventoryRepository.list_inventory(
            db,
            page=page,
            page_size=page_size,
            query=query,
            low_stock_only=low_stock_only,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        read_items = [to_inventory_read(i) for i in items]

        return PaginatedInventoryResponse(
            items=read_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            low_stock_count=low_count,
        )

    @classmethod
    def get_low_stock_items(cls, db: Session, limit: int = 20) -> List[InventoryRead]:
        items = InventoryRepository.get_low_stock_items(db, limit=limit)
        return [to_inventory_read(i) for i in items]

    @classmethod
    def get_history(
        cls, db: Session, book_id: int, limit: int = 50
    ) -> List[InventoryTransactionRead]:
        inv = InventoryRepository.get_by_book_id(db, book_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy bản ghi tồn kho cho sách ID {book_id}.",
            )
        txs = InventoryRepository.get_history(db, inv.id, limit=limit)
        return [InventoryTransactionRead.model_validate(t) for t in txs]

    @classmethod
    def inbound_restock(
        cls, db: Session, data: InventoryInboundRequest, staff_user: User
    ) -> InventoryRead:
        book = db.query(Book).filter(Book.id == data.book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sách ID {data.book_id} không tồn tại.",
            )

        try:
            inv = InventoryRepository.inbound_restock(
                db=db,
                book_id=data.book_id,
                quantity=data.quantity,
                reference_code=data.reference_code,
                reason=data.reason or "Nhập kho định kỳ",
                staff_user_id=staff_user.id,
            )
            # If book was marked OUT_OF_STOCK, return it to ACTIVE
            if book.status == "OUT_OF_STOCK" and (inv.physical_stock - inv.reserved_stock) > 0:
                book.status = "ACTIVE"
                db.commit()

            return to_inventory_read(inv)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @classmethod
    def adjust_stock(
        cls, db: Session, data: InventoryAdjustmentRequest, staff_user: User
    ) -> InventoryRead:
        book = db.query(Book).filter(Book.id == data.book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sách ID {data.book_id} không tồn tại.",
            )

        try:
            inv = InventoryRepository.adjust_stock(
                db=db,
                book_id=data.book_id,
                delta=data.quantity_change,
                reference_code=data.reference_code,
                reason=data.reason,
                staff_user_id=staff_user.id,
            )
            # Update book status if stock drops to 0
            if (inv.physical_stock - inv.reserved_stock) <= 0:
                book.status = "OUT_OF_STOCK"
                db.commit()
            elif book.status == "OUT_OF_STOCK" and (inv.physical_stock - inv.reserved_stock) > 0:
                book.status = "ACTIVE"
                db.commit()

            return to_inventory_read(inv)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
