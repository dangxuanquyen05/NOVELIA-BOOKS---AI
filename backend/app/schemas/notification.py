"""Pydantic schemas for In-App Notifications and User Alerts."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class NotificationBase(BaseModel):
    """Common notification fields."""

    title: str = Field(..., max_length=150, description="Short notification title")
    message: str = Field(..., description="Notification body content")
    notification_type: str = Field(
        ...,
        max_length=50,
        description="Type category: ORDER, SHIPPING, PROMOTION, SYSTEM, INVENTORY",
    )
    reference_link: Optional[str] = Field(
        None, max_length=255, description="Deep link path (e.g. /orders/NVL-123)"
    )


class NotificationCreate(NotificationBase):
    """Creation payload for an individual notification."""

    user_id: int = Field(..., description="Target user ID")


class BroadcastNotificationCreate(NotificationBase):
    """Administrative payload to broadcast an announcement."""

    target_role: Optional[str] = Field(
        None, description="Optional target role (e.g. CUSTOMER, STAFF, or None for all)"
    )


class NotificationRead(NotificationBase):
    """Serialized notification representation."""

    id: int
    user_id: int
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    """Paginated list of notifications with unread tally."""

    items: List[NotificationRead]
    total: int
    unread_count: int
    page: int
    limit: int


class UnreadCountResponse(BaseModel):
    """Simple counter response for navbar notification badges."""

    unread_count: int


class MarkReadResponse(BaseModel):
    """Confirmation of marking notifications as read."""

    success: bool
    marked_count: int
    message: str
