"""Shipment repository handling database operations for logistics and tracking."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session, selectinload

from app.models.commerce import Order
from app.models.payment_shipping import Shipment, ShipmentEvent


class ShipmentRepository:
    """Encapsulates ACID database operations for Shipments and ShipmentEvents."""

    @classmethod
    def create_shipment(
        cls,
        db: Session,
        order: Order,
        carrier: str,
        tracking_code: str,
        shipping_fee: Decimal = Decimal("0.00"),
        estimated_delivery_date: Optional[date] = None,
    ) -> Shipment:
        """Create new shipment logistics record linked to an Order."""
        shipment = Shipment(
            order_id=order.id,
            carrier=carrier.upper(),
            tracking_code=tracking_code,
            shipping_fee=shipping_fee,
            status="READY_TO_PICK",
            estimated_delivery_date=estimated_delivery_date,
            dispatched_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(shipment)
        db.flush()
        return shipment

    @classmethod
    def get_by_id(cls, db: Session, shipment_id: int) -> Optional[Shipment]:
        return (
            db.query(Shipment)
            .options(selectinload(Shipment.events), selectinload(Shipment.order))
            .filter(Shipment.id == shipment_id)
            .first()
        )

    @classmethod
    def get_by_order_id(cls, db: Session, order_id: int) -> Optional[Shipment]:
        return (
            db.query(Shipment)
            .options(selectinload(Shipment.events), selectinload(Shipment.order))
            .filter(Shipment.order_id == order_id)
            .first()
        )

    @classmethod
    def get_by_order_code(cls, db: Session, order_code: str) -> Optional[Shipment]:
        return (
            db.query(Shipment)
            .join(Order, Shipment.order_id == Order.id)
            .options(selectinload(Shipment.events), selectinload(Shipment.order))
            .filter(Order.order_code == order_code)
            .first()
        )

    @classmethod
    def get_by_tracking_code(cls, db: Session, tracking_code: str) -> Optional[Shipment]:
        return (
            db.query(Shipment)
            .options(selectinload(Shipment.events), selectinload(Shipment.order))
            .filter(Shipment.tracking_code == tracking_code)
            .first()
        )

    @classmethod
    def add_event(
        cls,
        db: Session,
        shipment_id: int,
        status: str,
        description: str,
        location: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
        occurred_at: Optional[datetime] = None,
    ) -> ShipmentEvent:
        """Record tracking milestone event."""
        event = ShipmentEvent(
            shipment_id=shipment_id,
            status=status.upper(),
            description=description,
            location=location,
            raw_payload=raw_payload,
            occurred_at=occurred_at or datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.flush()
        return event

    @classmethod
    def has_event_occurred(
        cls,
        db: Session,
        shipment_id: int,
        status: str,
        occurred_at: Optional[datetime] = None,
    ) -> bool:
        """Check for existing duplicate webhook event to protect against replay."""
        q = db.query(ShipmentEvent).filter(
            ShipmentEvent.shipment_id == shipment_id,
            ShipmentEvent.status == status.upper(),
        )
        if occurred_at:
            q = q.filter(ShipmentEvent.occurred_at == occurred_at)
        return q.first() is not None

    @classmethod
    def update_shipment_status(
        cls,
        db: Session,
        shipment: Shipment,
        status: str,
        dispatched_at: Optional[datetime] = None,
        delivered_at: Optional[datetime] = None,
    ) -> Shipment:
        """Update lifecycle status and milestone dates."""
        shipment.status = status.upper()
        shipment.updated_at = datetime.now(timezone.utc)
        if dispatched_at:
            shipment.dispatched_at = dispatched_at
        if delivered_at:
            shipment.delivered_at = delivered_at
        db.flush()
        return shipment
