"""Customer experience models: Reviews and Notifications."""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Review(Base):
    """Customer book reviews and 1-5 star ratings."""

    __tablename__ = "reviews"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    
    rating = Column(Integer, nullable=False)  # 1 to 5
    title = Column(String(150), nullable=True)
    comment = Column(Text, nullable=False)
    is_verified_purchase = Column(Boolean, default=False, nullable=False)
    status = Column(String(30), default="APPROVED", nullable=False, index=True)  # PENDING, APPROVED, HIDDEN
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_user_book_review"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_review_rating_1_to_5"),
        Index("idx_reviews_book", "book_id"),
        Index("idx_reviews_user", "user_id"),
        Index("idx_reviews_rating", "rating"),
        Index("idx_reviews_status", "status"),
    )

    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")
    order = relationship("Order")


class Notification(Base):
    """In-app notifications for users (orders, promotions, system announcements)."""

    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False, index=True)  # ORDER, PROMOTION, SYSTEM, INVENTORY
    reference_link = Column(String(255), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "is_read"),
        Index("idx_notifications_created", "created_at"),
    )

    user = relationship("User", back_populates="notifications")
