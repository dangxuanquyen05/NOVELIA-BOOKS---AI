"""Customer in-app notification service with deduplication and order lifecycle hooks."""

import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.commerce import Order
from app.models.payment_shipping import Shipment
from app.repositories.notification_repo import NotificationRepository
from app.schemas.notification import (
    MarkReadResponse,
    NotificationListResponse,
    NotificationRead,
    UnreadCountResponse,
)
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

ORDER_STATUS_MESSAGES = {
    "CONFIRMED": ("Đơn hàng đã được xác nhận", "Đơn hàng {code} của bạn đã được cửa hàng xác nhận và chuẩn bị xuất kho."),
    "PROCESSING": ("Đơn hàng đang xử lý", "Các cuốn sách trong đơn {code} đang được đóng gói cẩn thận."),
    "SHIPPING": ("Đơn hàng đang được giao", "Đơn hàng {code} đã được bàn giao cho đối tác vận chuyển."),
    "COMPLETED": ("Giao hàng thành công", "Đơn hàng {code} đã giao thành công. Chúc bạn có những giờ phút đọc sách thú vị!"),
    "CANCELLED": ("Đơn hàng đã hủy", "Đơn hàng {code} đã được hủy bỏ. Lý do: {reason}"),
}


class NotificationService:
    """Service layer orchestrating customer notifications and multi-channel delivery."""

    @classmethod
    def get_user_notifications(
        cls,
        db: Session,
        user_id: int,
        is_read: Optional[bool] = None,
        notification_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> NotificationListResponse:
        """Fetch paginated notifications scoped strictly to caller user_id."""
        offset = max(0, (page - 1) * limit)
        items, total, unread = NotificationRepository.get_user_notifications(
            db=db,
            user_id=user_id,
            is_read=is_read,
            notification_type=notification_type,
            limit=limit,
            offset=offset,
        )

        return NotificationListResponse(
            items=[NotificationRead.model_validate(it) for it in items],
            total=total,
            unread_count=unread,
            page=page,
            limit=limit,
        )

    @classmethod
    def get_unread_count(cls, db: Session, user_id: int) -> UnreadCountResponse:
        """Return badge counter for navbar."""
        count = NotificationRepository.get_unread_count(db, user_id)
        return UnreadCountResponse(unread_count=count)

    @classmethod
    def mark_as_read(
        cls, db: Session, notification_id: int, user_id: int
    ) -> NotificationRead:
        """Mark single notification as read with tenant authorization."""
        notif = NotificationRepository.mark_as_read(db, notification_id, user_id)
        if not notif:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thông báo không tồn tại hoặc bạn không có quyền truy cập.",
            )
        return NotificationRead.model_validate(notif)

    @classmethod
    def mark_all_as_read(cls, db: Session, user_id: int) -> MarkReadResponse:
        """Mark all unread notifications of caller as read."""
        count = NotificationRepository.mark_all_as_read(db, user_id)
        return MarkReadResponse(
            success=True,
            marked_count=count,
            message=f"Đã đánh dấu {count} thông báo là đã đọc.",
        )

    @classmethod
    def notify_order_status_change(
        cls,
        db: Session,
        order: Order,
        old_status: Optional[str],
        new_status: str,
        notes: Optional[str] = None,
    ) -> Optional[NotificationRead]:
        """Trigger in-app notification and email on order status transitions with replay protection."""
        if not order.user_id:
            return None

        status_key = new_status.strip().upper()
        default_title = f"Cập nhật đơn hàng #{order.order_code}"
        default_msg = f"Đơn hàng của bạn đã chuyển sang trạng thái {status_key}."

        title_tpl, msg_tpl = ORDER_STATUS_MESSAGES.get(
            status_key, (default_title, default_msg)
        )
        title = title_tpl.format(code=order.order_code)
        message = msg_tpl.format(code=order.order_code, reason=notes or "Không có lý do chi tiết")

        ref_link = f"/orders/{order.order_code}"

        # Deduplication check: Avoid multiple notifications for same state within 10 minutes
        if NotificationRepository.has_similar_notification_recently(
            db,
            user_id=order.user_id,
            notification_type="ORDER",
            reference_link=ref_link,
            title=title,
            within_minutes=10,
        ):
            logger.info(f"Notification for order {order.order_code} status {new_status} deduplicated.")
            return None

        # Create in-app notification
        notif = NotificationRepository.create_notification(
            db=db,
            user_id=order.user_id,
            title=title,
            message=message,
            notification_type="ORDER",
            reference_link=ref_link,
        )

        # Dispatch email asynchronously/gracefully if user email exists
        if order.user and order.user.email:
            try:
                EmailService.send_order_status_email(
                    order=order,
                    recipient_email=order.user.email,
                    new_status=new_status,
                    notes=notes,
                )
            except Exception as e:
                logger.warning(f"Failed to dispatch status email for {order.order_code}: {e}")

        return NotificationRead.model_validate(notif)

    @classmethod
    def notify_shipping_update(
        cls,
        db: Session,
        shipment: Shipment,
        carrier_status: str,
        description: str,
    ) -> Optional[NotificationRead]:
        """Trigger in-app shipping milestone notification with deduplication."""
        if not shipment.order or not shipment.order.user_id:
            return None

        order = shipment.order
        title = f"Vận chuyển đơn hàng #{order.order_code}"
        message = f"Vận đơn {shipment.tracking_code} ({shipment.carrier}): {description}"
        ref_link = f"/orders/{order.order_code}"

        if NotificationRepository.has_similar_notification_recently(
            db,
            user_id=order.user_id,
            notification_type="SHIPPING",
            reference_link=ref_link,
            title=title,
            within_minutes=10,
        ):
            return None

        notif = NotificationRepository.create_notification(
            db=db,
            user_id=order.user_id,
            title=title,
            message=message,
            notification_type="SHIPPING",
            reference_link=ref_link,
        )

        if order.user and order.user.email:
            try:
                EmailService.send_shipping_update_email(
                    shipment=shipment,
                    recipient_email=order.user.email,
                    status_desc=description,
                )
            except Exception as e:
                logger.warning(f"Failed to dispatch shipping update email: {e}")

        return NotificationRead.model_validate(notif)

    @classmethod
    def broadcast_announcement(
        cls,
        db: Session,
        title: str,
        message: str,
        notification_type: str = "SYSTEM",
        reference_link: Optional[str] = None,
        target_role: Optional[str] = None,
    ) -> int:
        """Administrative feature to broadcast announcements to customers or staff."""
        return NotificationRepository.broadcast_notification(
            db=db,
            title=title,
            message=message,
            notification_type=notification_type,
            reference_link=reference_link,
            target_role=target_role,
        )
