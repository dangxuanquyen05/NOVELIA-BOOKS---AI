"""Repository for managing in-app customer notifications with tenant isolation and deduplication."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.experience import Notification
from app.models.user import Role, User


class NotificationRepository:
    """Data access layer for in-app notifications and customer alerts."""

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Notification], int, int]:
        """Fetch paginated notifications strictly scoped to user_id.

        Returns:
            Tuple of (items, total_count, unread_count)
        """
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        if notification_type:
            query = query.filter(
                Notification.notification_type == notification_type.strip().upper()
            )

        total_count = query.count()
        unread_count = (
            db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .scalar()
            or 0
        )

        items = (
            query.order_by(desc(Notification.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
        return items, total_count, unread_count

    @staticmethod
    def get_unread_count(db: Session, user_id: int) -> int:
        """Count unread notifications for a specific user."""
        return (
            db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .scalar()
            or 0
        )

    @staticmethod
    def mark_as_read(
        db: Session, notification_id: int, user_id: int
    ) -> Optional[Notification]:
        """Mark a notification as read with strict tenant isolation."""
        notification = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )
        if not notification:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(notification)

        return notification

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int) -> int:
        """Mark all unread notifications of a user as read."""
        now = datetime.now(timezone.utc)
        updated_rows = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update(
                {Notification.is_read: True, Notification.read_at: now},
                synchronize_session=False,
            )
        )
        db.commit()
        return updated_rows

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        reference_link: Optional[str] = None,
    ) -> Notification:
        """Persist a single in-app notification."""
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type.strip().upper(),
            reference_link=reference_link,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def has_similar_notification_recently(
        db: Session,
        user_id: int,
        notification_type: str,
        reference_link: Optional[str],
        title: str,
        within_minutes: int = 60,
    ) -> bool:
        """Check if an identical notification was recently dispatched (replay protection)."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=within_minutes)
        query = db.query(Notification.id).filter(
            Notification.user_id == user_id,
            Notification.notification_type == notification_type.strip().upper(),
            Notification.title == title,
            Notification.created_at >= cutoff,
        )
        if reference_link:
            query = query.filter(Notification.reference_link == reference_link)

        return query.first() is not None

    @staticmethod
    def broadcast_notification(
        db: Session,
        title: str,
        message: str,
        notification_type: str,
        reference_link: Optional[str] = None,
        target_role: Optional[str] = None,
    ) -> int:
        """Broadcast announcement to multiple active users (ADMIN/STAFF feature)."""
        users_query = db.query(User.id).filter(User.is_active == True)
        if target_role:
            users_query = users_query.join(User.roles).filter(
                Role.name == target_role.strip().upper()
            )

        user_ids = [uid[0] for uid in users_query.all()]
        now = datetime.now(timezone.utc)

        notifications = [
            Notification(
                user_id=uid,
                title=title,
                message=message,
                notification_type=notification_type.strip().upper(),
                reference_link=reference_link,
                is_read=False,
                created_at=now,
            )
            for uid in user_ids
        ]

        if notifications:
            db.bulk_save_objects(notifications)
            db.commit()

        return len(notifications)
