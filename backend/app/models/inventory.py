"""Inventory stock and audit transaction models."""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Inventory(Base):
    """Real-time stock tracking per book with reservation support."""

    __tablename__ = "inventory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), unique=True, nullable=False)
    physical_stock = Column(Integer, default=0, nullable=False)
    reserved_stock = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=10, nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("physical_stock >= reserved_stock", name="chk_inventory_non_negative"),
        CheckConstraint("physical_stock >= 0", name="chk_physical_non_negative"),
        CheckConstraint("reserved_stock >= 0", name="chk_reserved_non_negative"),
        Index("idx_inventory_book", "book_id"),
    )

    @property
    def available_stock(self) -> int:
        """Calculate available stock ready for purchase."""
        return self.physical_stock - self.reserved_stock

    book = relationship("Book", back_populates="inventory")
    transactions = relationship("InventoryTransaction", back_populates="inventory", cascade="all, delete-orphan")


class InventoryTransaction(Base):
    """Audit trail for every stock mutation (Import, Hold, Release, Export, Adjustment)."""

    __tablename__ = "inventory_transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    inventory_id = Column(BigInteger, ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False)
    transaction_type = Column(String(50), nullable=False, index=True)  # IMPORT, EXPORT, ORDER_HOLD, ORDER_RELEASE, ADJUSTMENT
    quantity_change = Column(Integer, nullable=False)
    stock_after = Column(Integer, nullable=False)
    reference_code = Column(String(100), nullable=True, index=True)
    notes = Column(String(255), nullable=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_inv_trans_inventory", "inventory_id"),
        Index("idx_inv_trans_created_at", "created_at"),
    )

    inventory = relationship("Inventory", back_populates="transactions")
    created_by = relationship("User")
