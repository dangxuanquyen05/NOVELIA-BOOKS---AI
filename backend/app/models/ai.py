"""AI ecosystem models: Conversations, Messages, Action Logs, Interaction Events, and Recommendations."""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class AIConversation(Base):
    """Chat session for Novelia AI Assistant or BookMatch AI."""

    __tablename__ = "ai_conversations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_uuid = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    conversation_type = Column(String(50), default="ASSISTANT", nullable=False)  # ASSISTANT, BOOKMATCH
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_ai_conversations_user", "user_id"),
        Index("idx_ai_conversations_created", "created_at"),
    )

    user = relationship("User")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")
    action_logs = relationship("AIActionLog", back_populates="conversation")


class AIMessage(Base):
    """Dialogue turn in an AI conversation."""

    __tablename__ = "ai_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False)  # USER, ASSISTANT, SYSTEM, TOOL
    content = Column(Text, nullable=False)
    tool_calls = Column(JSON, nullable=True)
    tool_results = Column(JSON, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_ai_messages_conv", "conversation_id"),
        Index("idx_ai_messages_created", "created_at"),
    )

    conversation = relationship("AIConversation", back_populates="messages")


class AIActionLog(Base):
    """Persistent audit log of every tool execution with RBAC security context and two-phase mutations."""

    __tablename__ = "ai_action_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(BigInteger, ForeignKey("ai_conversations.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_role = Column(String(50), nullable=False)
    tool_name = Column(String(100), nullable=False, index=True)
    input_arguments = Column(JSON, nullable=False)
    execution_status = Column(String(50), nullable=False, index=True)  # SUCCESS, REJECTED_RBAC, FAILED_VALIDATION, ERROR, CONFIRMATION_REQUIRED
    confirmation_token = Column(String(100), nullable=True, index=True)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    output_summary = Column(Text, nullable=True)
    execution_duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_ai_actions_user", "user_id"),
        Index("idx_ai_actions_tool", "tool_name"),
        Index("idx_ai_actions_status", "execution_status"),
        Index("idx_ai_actions_token", "confirmation_token"),
    )

    conversation = relationship("AIConversation", back_populates="action_logs")
    user = relationship("User")


class UserBookEvent(Base):
    """Behavioral telemetry for recommendation engines and personalized discovery."""

    __tablename__ = "user_book_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False, index=True)  # VIEW, SEARCH_CLICK, ADD_TO_CART, WISHLIST, PURCHASE
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_events_user", "user_id"),
        Index("idx_events_book", "book_id"),
        Index("idx_events_type_created", "event_type", "created_at"),
    )

    user = relationship("User")
    book = relationship("Book")


class BookRecommendation(Base):
    """Precomputed or dynamic recommendation items for users."""

    __tablename__ = "book_recommendations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    algorithm_type = Column(String(50), nullable=False)  # COLLABORATIVE, CONTENT_BASED, BOOKMATCH_AI, TRENDING
    score = Column(DECIMAL(5, 4), nullable=False)  # Normalized score 0.0000 to 1.0000
    reason = Column(String(255), nullable=True)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", "algorithm_type", name="uq_user_book_rec"),
        CheckConstraint("score >= 0.0000 AND score <= 1.0000", name="chk_rec_score_range"),
        Index("idx_recs_user", "user_id"),
        Index("idx_recs_algo_score", "algorithm_type", "score"),
    )

    user = relationship("User")
    book = relationship("Book")
