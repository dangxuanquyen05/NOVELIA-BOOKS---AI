"""Email dispatch service with safe retry, templating, and graceful degradation.

Non-negotiable rule: Any transport, connection, or SMTP error must NEVER
fail an order, disrupt a transaction, or bubble up as an unhandled HTTP 500 error.
"""

import logging
import time
from typing import Any, Dict, Optional

from app.integrations.email.base import (
    EmailDeliveryResult,
    EmailMessage,
)
from app.integrations.email.factory import get_email_provider
from app.models.commerce import Order
from app.models.payment_shipping import Shipment

logger = logging.getLogger(__name__)


class EmailService:
    """Business logic for dispatching transactional customer emails."""

    @classmethod
    def send_transactional_email(
        cls,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        reference_id: Optional[str] = None,
        max_retries: int = 2,
    ) -> EmailDeliveryResult:
        """Send an email with safe exponential backoff retry and zero-fail safety.

        Guarantees that an SMTP failure does not abort an order transaction.
        """
        provider = get_email_provider()
        message = EmailMessage(
            to_email=to_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            reference_id=reference_id,
        )

        last_result: Optional[EmailDeliveryResult] = None

        for attempt in range(max_retries + 1):
            try:
                result = provider.send_email(message)
                if result.success:
                    return result

                last_result = result
                logger.warning(
                    f"Email dispatch attempt {attempt + 1}/{max_retries + 1} failed: {result.error}"
                )
            except Exception as e:
                logger.error(f"Unexpected email transport exception: {str(e)}")
                last_result = EmailDeliveryResult(
                    success=False,
                    message_id="err_transport",
                    provider_type="ERROR",
                    is_mock=False,
                    recipient=to_email,
                    subject=subject,
                    error=str(e),
                )

            # Exponential backoff delay if retrying
            if attempt < max_retries:
                time.sleep(0.05 * (2**attempt))

        return last_result or EmailDeliveryResult(
            success=False,
            message_id="err_exhausted",
            provider_type="UNKNOWN",
            is_mock=False,
            recipient=to_email,
            subject=subject,
            error="Exhausted all email dispatch attempts.",
        )

    @classmethod
    def send_order_confirmation_email(cls, order: Order, recipient_email: str) -> EmailDeliveryResult:
        """Send customer order receipt upon checkout."""
        subject = f"[NOVELIA BOOKS] Xác nhận đơn hàng thành công #{order.order_code}"
        items_summary = "\n".join(
            [f"- {it.title} x {it.quantity} = {int(it.subtotal):,} VND" for it in order.items]
        )
        body_text = (
            f"Kính chào quý khách,\n\n"
            f"Đơn hàng {order.order_code} của quý khách đã được ghi nhận thành công trên hệ thống Novelia Books.\n\n"
            f"Chi tiết sản phẩm:\n{items_summary}\n\n"
            f"Tổng tiền thanh toán: {int(order.final_amount):,} VND\n"
            f"Phương thức thanh toán: {order.payment.payment_method if order.payment else 'COD'}\n\n"
            f"Cảm ơn quý khách đã tin tưởng và đồng hành cùng Novelia Books!"
        )
        body_html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; rounded: 8px;">
            <h2 style="color: #b45309;">Novelia Books — Xác Nhận Đơn Hàng</h2>
            <p>Kính chào quý khách,</p>
            <p>Đơn hàng <strong>{order.order_code}</strong> của quý khách đã được ghi nhận trên hệ thống.</p>
            <div style="background: #f8fafc; padding: 15px; border-radius: 6px; margin: 15px 0;">
                <p><strong>Tổng thanh toán:</strong> {int(order.final_amount):,} VND</p>
                <p><strong>Trạng thái:</strong> {order.status}</p>
            </div>
            <p>Quý khách có thể theo dõi đơn hàng bất kỳ lúc nào trên ứng dụng Novelia Books.</p>
        </div>
        """
        return cls.send_transactional_email(
            to_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            reference_id=order.order_code,
        )

    @classmethod
    def send_order_status_email(
        cls, order: Order, recipient_email: str, new_status: str, notes: Optional[str] = None
    ) -> EmailDeliveryResult:
        """Send customer notification when order progresses through lifecycle."""
        status_labels = {
            "CONFIRMED": "Đã được xác nhận",
            "PROCESSING": "Đang đóng gói và chuẩn bị xuất kho",
            "SHIPPING": "Đang được giao đến bạn",
            "COMPLETED": "Đã giao hàng thành công",
            "CANCELLED": "Đã bị hủy",
        }
        status_text = status_labels.get(new_status, new_status)
        subject = f"[NOVELIA BOOKS] Cập nhật đơn hàng #{order.order_code} — {status_text}"

        body_text = (
            f"Kính chào quý khách,\n\n"
            f"Đơn hàng {order.order_code} của quý khách hiện tại: {status_text}.\n"
            f"{f'Ghi chú: {notes}' if notes else ''}\n\n"
            f"Quý khách có thể truy cập lịch sử đơn hàng để xem chi tiết.\n"
            f"Trân trọng,\nĐội ngũ Novelia Books"
        )
        body_html = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0;">
            <h2 style="color: #b45309;">Novelia Books — Cập Nhật Đơn Hàng</h2>
            <p>Đơn hàng <strong>{order.order_code}</strong> của bạn: <strong>{status_text}</strong>.</p>
            {f'<p style="color: #64748b;">Ghi chú: {notes}</p>' if notes else ''}
        </div>
        """
        return cls.send_transactional_email(
            to_email=recipient_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            reference_id=order.order_code,
        )

    @classmethod
    def send_shipping_update_email(
        cls, shipment: Shipment, recipient_email: str, status_desc: str
    ) -> EmailDeliveryResult:
        """Send delivery milestone update."""
        order_code = shipment.order.order_code if shipment.order else ""
        subject = f"[NOVELIA BOOKS] Thông tin vận chuyển đơn #{order_code} ({shipment.tracking_code})"
        body_text = (
            f"Đơn hàng {order_code} của bạn với mã vận đơn {shipment.tracking_code} (Hãng {shipment.carrier}):\n"
            f"Trạng thái: {status_desc}\n\n"
            f"Quý khách có thể theo dõi trực tiếp trên website Novelia Books."
        )
        return cls.send_transactional_email(
            to_email=recipient_email,
            subject=subject,
            body_text=body_text,
            reference_id=shipment.tracking_code,
        )
