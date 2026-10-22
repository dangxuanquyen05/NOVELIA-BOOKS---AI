"""Repository for real-time inventory management, stock mutations, and audit logging."""

from typing import List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.catalog import Book
from app.models.inventory import Inventory, InventoryTransaction


class InventoryRepository:
    """Data access layer for stock management, restock imports, and transaction logging."""

    @staticmethod
    def get_by_book_id(db: Session, book_id: int) -> Optional[Inventory]:
        return (
            db.query(Inventory)
            .options(selectinload(Inventory.book))
            .filter(Inventory.book_id == book_id)
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, inventory_id: int) -> Optional[Inventory]:
        return (
            db.query(Inventory)
            .options(selectinload(Inventory.book))
            .filter(Inventory.id == inventory_id)
            .first()
        )

    @staticmethod
    def list_inventory(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        query: Optional[str] = None,
        low_stock_only: bool = False,
    ) -> Tuple[List[Inventory], int, int]:
        """Fetch inventory with optional low-stock filter and keyword search."""
        q = db.query(Inventory).join(Book).options(selectinload(Inventory.book))

        if query:
            term = f"%{query.strip()}%"
            q = q.filter(
                or_(
                    Book.title.ilike(term),
                    Book.isbn.ilike(term),
                    Book.sku.ilike(term),
                )
            )

        if low_stock_only:
            # Physical - Reserved <= Threshold
            q = q.filter(
                (Inventory.physical_stock - Inventory.reserved_stock)
                <= Inventory.low_stock_threshold
            )

        total = q.count()

        # Count total low stock items overall
        low_stock_count = (
            db.query(Inventory)
            .filter(
                (Inventory.physical_stock - Inventory.reserved_stock)
                <= Inventory.low_stock_threshold
            )
            .count()
        )

        offset = (page - 1) * page_size
        items = q.order_by(
            (Inventory.physical_stock - Inventory.reserved_stock).asc()
        ).offset(offset).limit(page_size).all()

        return items, total, low_stock_count

    @staticmethod
    def get_low_stock_items(db: Session, limit: int = 20) -> List[Inventory]:
        """Fetch items where available stock is below or at safety threshold."""
        return (
            db.query(Inventory)
            .join(Book)
            .options(selectinload(Inventory.book))
            .filter(
                (Inventory.physical_stock - Inventory.reserved_stock)
                <= Inventory.low_stock_threshold
            )
            .order_by((Inventory.physical_stock - Inventory.reserved_stock).asc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_history(
        db: Session, inventory_id: int, limit: int = 50
    ) -> List[InventoryTransaction]:
        """Fetch chronological audit trail of stock mutations."""
        return (
            db.query(InventoryTransaction)
            .filter(InventoryTransaction.inventory_id == inventory_id)
            .order_by(InventoryTransaction.created_at.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def inbound_restock(
        cls,
        db: Session,
        book_id: int,
        quantity: int,
        reference_code: str,
        reason: str,
        staff_user_id: int,
    ) -> Inventory:
        """Process inbound inventory restock and record immutable transaction."""
        inventory = cls.get_by_book_id(db, book_id)
        if not inventory:
            raise ValueError(f"Bản ghi tồn kho cho sách ID {book_id} không tồn tại.")

        inventory.physical_stock += quantity
        new_balance = inventory.physical_stock

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="IMPORT",
            quantity_change=quantity,
            balance_after=new_balance,
            reference_code=reference_code,
            reason=reason,
            staff_user_id=staff_user_id,
        )
        db.add(tx)
        db.commit()
        db.refresh(inventory)
        return inventory

    @classmethod
    def adjust_stock(
        cls,
        db: Session,
        book_id: int,
        delta: int,
        reference_code: str,
        reason: str,
        staff_user_id: int,
    ) -> Inventory:
        """Apply manual stock adjustment with non-negative physical stock constraint."""
        inventory = cls.get_by_book_id(db, book_id)
        if not inventory:
            raise ValueError(f"Bản ghi tồn kho cho sách ID {book_id} không tồn tại.")

        if inventory.physical_stock + delta < 0:
            raise ValueError("Số lượng tồn kho vật lý không thể âm.")

        if inventory.physical_stock + delta < inventory.reserved_stock:
            raise ValueError(
                f"Tồn kho sau điều chỉnh ({inventory.physical_stock + delta}) không thể nhỏ hơn tồn kho giữ chỗ ({inventory.reserved_stock})."
            )

        inventory.physical_stock += delta
        new_balance = inventory.physical_stock

        tx = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type="ADJUSTMENT",
            quantity_change=delta,
            balance_after=new_balance,
            reference_code=reference_code,
            reason=reason,
            staff_user_id=staff_user_id,
        )
        db.add(tx)
        db.commit()
        db.refresh(inventory)
        return inventory
