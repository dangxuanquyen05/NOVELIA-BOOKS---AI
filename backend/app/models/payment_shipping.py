"""Payment and shipping models: Payments, RefundRequests, Shipments, and ShipmentEvents."""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Payment(Base):
    """Payment transaction record for an order."""

    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    payment_code = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="RESTRICT"), unique=True, nullable=False)
    
    # Method: COD, VNPAY, MOMO, ZALOPAY, BANK_TRANSFER
    payment_method = Column(String(30), nullable=False)
    
    # Status: PENDING, PAID, FAILED, REFUNDED
    payment_status = Column(String(30), default="PENDING", nullable=False, index=True)
    
    amount = Column(DECIMAL(12, 2), nullable=False)
    transaction_id = Column(String(100), nullable=True, index=True)  # Gateway reference code
    gateway_response = Column(JSON, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_payments_order", "order_id"),
        Index("idx_payments_status", "payment_status"),
        Index("idx_payments_method", "payment_method"),
        CheckConstraint("amount >= 0", name="chk_payment_amount_non_negative"),
    )

    order = relationship("Order", back_populates="payment")
    refunds = relationship("RefundRequest", back_populates="payment")


class RefundRequest(Base):
    """Customer refund request and administrative reconciliation."""

    __tablename__ = "refund_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    refund_code = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False)
    payment_id = Column(BigInteger, ForeignKey("payments.id", ondelete="RESTRICT"), nullable=True)
    
    amount = Column(DECIMAL(12, 2), nullable=False)
    reason = Column(Text, nullable=False)
    
    # Status: PENDING, APPROVED, REJECTED, COMPLETED
    status = Column(String(30), default="PENDING", nullable=False, index=True)
    
    admin_notes = Column(Text, nullable=True)
    processed_by_user_id = Column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_refunds_order", "order_id"),
        Index("idx_refunds_status", "status"),
        CheckConstraint("amount > 0", name="chk_refund_amount_positive"),
    )

    order = relationship("Order")
    payment = relationship("Payment", back_populates="refunds")
    processed_by = relationship("User")


class Shipment(Base):
    """Logistics and delivery record connecting to third-party shipping carriers."""

    __tablename__ = "shipments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tracking_code = Column(String(100), unique=True, nullable=True, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="RESTRICT"), unique=True, nullable=False)
    
    carrier = Column(String(50), nullable=False)  # GHN, GHTK, INTERNAL
    shipping_service_id = Column(String(50), nullable=True)
    shipping_fee = Column(DECIMAL(12, 2), default=0.00, nullable=False)
    
    # Status: PENDING, READY_TO_PICK, PICKING, IN_TRANSIT, DELIVERED, RETURNED, FAILED
    status = Column(String(30), default="PENDING", nullable=False, index=True)
    
    estimated_delivery_date = Column(Date, nullable=True)
    dispatched_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_shipments_order", "order_id"),
        Index("idx_shipments_status", "status"),
        Index("idx_shipments_carrier", "carrier"),
        CheckConstraint("shipping_fee >= 0", name="chk_shipment_fee_non_negative"),
    )

    order = relationship("Order", back_populates="shipment")
    events = relationship("ShipmentEvent", back_populates="shipment", cascade="all, delete-orphan")


class ShipmentEvent(Base):
    """Carrier webhook status checkpoints and telemetry."""

    __tablename__ = "shipment_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shipment_id = Column(BigInteger, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), nullable=False)
    location = Column(String(255), nullable=True)
    description = Column(String(255), nullable=False)
    raw_payload = Column(JSON, nullable=True)
    occurred_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_shipment_events_shipment", "shipment_id"),
        Index("idx_shipment_events_occurred", "occurred_at"),
    )

    shipment = relationship("Shipment", back_populates="events")
