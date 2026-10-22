"""Order and OrderItem database repository."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.commerce import Order, OrderItem
from app.models.payment_shipping import Payment


class OrderRepository:
    """Data access layer for Orders, OrderItems, and Order Payments."""

    @staticmethod
    def get_by_id(db: Session, order_id: int) -> Optional[Order]:
        return (
            db.query(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment),
                selectinload(Order.shipment),
                selectinload(Order.coupon_usages),
            )
            .filter(Order.id == order_id)
            .first()
        )

    @staticmethod
    def get_by_code(
        db: Session, order_code: str, user_id: Optional[int] = None
    ) -> Optional[Order]:
        """Fetch order by code with eager-loaded items and payment.

        If user_id is provided, strictly enforces tenant isolation.
        """
        q = (
            db.query(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment),
                selectinload(Order.shipment),
                selectinload(Order.coupon_usages),
            )
            .filter(Order.order_code == order_code)
        )
        if user_id is not None:
            q = q.filter(Order.user_id == user_id)
        return q.first()

    @staticmethod
    def find_by_idempotency_key(
        db: Session, user_id: int, idempotency_key: str
    ) -> Optional[Order]:
        """Check if an order was already created with this idempotency key."""
        marker = f"IDEMPOTENCY:{idempotency_key.strip()}"
        return (
            db.query(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment),
                selectinload(Order.shipment),
            )
            .filter(
                Order.user_id == user_id,
                Order.staff_notes.like(f"%{marker}%"),
            )
            .first()
        )

    @staticmethod
    def list_user_orders(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
    ) -> Tuple[List[Order], int]:
        """Retrieve paginated orders for a specific customer."""
        q = (
            db.query(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment),
                selectinload(Order.shipment),
            )
            .filter(Order.user_id == user_id)
        )
        if status and status.strip():
            q = q.filter(Order.status == status.strip().upper())

        total = q.count()
        offset = (page - 1) * page_size
        items = (
            q.order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def list_all_orders(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Tuple[List[Order], int]:
        """Retrieve paginated orders across all customers (Staff & Admin)."""
        q = db.query(Order).options(
            selectinload(Order.items),
            selectinload(Order.payment),
            selectinload(Order.shipment),
        )
        if status and status.strip():
            q = q.filter(Order.status == status.strip().upper())

        if query and query.strip():
            term = f"%{query.strip()}%"
            q = q.filter(
                or_(
                    Order.order_code.ilike(term),
                    Order.recipient_name.ilike(term),
                    Order.recipient_phone.ilike(term),
                )
            )

        total = q.count()
        offset = (page - 1) * page_size
        items = (
            q.order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def create_order(
        db: Session,
        order: Order,
        items: List[OrderItem],
        payment: Payment,
    ) -> Order:
        """Persist order, order line items, and payment within active transaction."""
        db.add(order)
        db.flush()  # Generate order.id
        if order.id is None:
            order.id = 1

        for item in items:
            item.order_id = order.id
            if item.id is None:
                item.id = 1
            db.add(item)

        payment.order_id = order.id
        if payment.id is None:
            payment.id = 1
        db.add(payment)
        db.flush()

        order.items = items
        order.payment = payment
        return order

    @staticmethod
    def update_order_status(
        db: Session,
        order: Order,
        new_status: str,
        staff_notes: Optional[str] = None,
        cancelled_reason: Optional[str] = None,
    ) -> Order:
        """Update order lifecycle status."""
        order.status = new_status
        if staff_notes:
            existing = order.staff_notes or ""
            order.staff_notes = f"{existing} | {staff_notes}".strip(" |")
        if cancelled_reason:
            order.cancelled_reason = cancelled_reason
        order.updated_at = datetime.now(timezone.utc)
        db.flush()
        return order
