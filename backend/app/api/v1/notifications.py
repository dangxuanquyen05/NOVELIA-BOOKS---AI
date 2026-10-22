"""Notification endpoints for customer in-app alerts and administrative announcements."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_roles
from app.models.user import User
from app.schemas.notification import (
    BroadcastNotificationCreate,
    MarkReadResponse,
    NotificationListResponse,
    NotificationRead,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List customer in-app notifications (Authenticated user)",
)
def get_my_notifications(
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    notification_type: Optional[str] = Query(
        None, description="Filter by category (ORDER, SHIPPING, PROMOTION, SYSTEM)"
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve notifications strictly scoped to authenticated user with unread tally."""
    return NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        is_read=is_read,
        notification_type=notification_type,
        page=page,
        limit=limit,
    )


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    summary="Get unread notification count badge (Authenticated user)",
)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Fetch unread count for navbar badge display."""
    return NotificationService.get_unread_count(db=db, user_id=current_user.id)


@router.put(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Mark single notification as read (Authenticated user)",
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark a notification as read with strict tenant isolation."""
    return NotificationService.mark_as_read(
        db=db, notification_id=notification_id, user_id=current_user.id
    )


@router.put(
    "/read-all",
    response_model=MarkReadResponse,
    summary="Mark all notifications as read (Authenticated user)",
)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Mark all unread notifications of the authenticated user as read."""
    return NotificationService.mark_all_as_read(db=db, user_id=current_user.id)


@router.post(
    "/broadcast",
    summary="Broadcast announcement to multiple users (STAFF/ADMIN only)",
    status_code=status.HTTP_201_CREATED,
)
def broadcast_announcement(
    payload: BroadcastNotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Publish a system-wide or role-targeted announcement."""
    dispatched_count = NotificationService.broadcast_announcement(
        db=db,
        title=payload.title,
        message=payload.message,
        notification_type=payload.notification_type,
        reference_link=payload.reference_link,
        target_role=payload.target_role,
    )
    return {
        "success": True,
        "dispatched_count": dispatched_count,
        "message": f"Đã gửi thông báo thành công đến {dispatched_count} người dùng.",
    }
