"""Business logic service for Phase 8 Shipping, Carrier Integrations, and Tracking Sync."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.shipping import (
    LiveIntegrationBlockedError,
    ShipmentCreationPayload,
    ShippingProviderError,
    get_shipping_provider,
)
from app.models.commerce import Order
from app.models.payment_shipping import Shipment, ShipmentEvent
from app.models.user import User
from app.repositories.order_repo import OrderRepository
from app.repositories.shipment_repo import ShipmentRepository
from app.repositories.user_repo import UserRepository
from app.schemas.shipping import (
    ShipmentDetailResponse,
    ShipmentDispatchCreateRequest,
    ShipmentEventResponse,
    ShipmentTrackingLookupResponse,
    ShippingProviderStatusResponse,
)

CARRIER_STATUS_LABELS = {
    "PENDING": "Chờ lấy hàng",
    "READY_TO_PICK": "Sẵn sàng lấy hàng",
    "PICKING": "Nhân viên đang lấy hàng",
    "IN_TRANSIT": "Đang vận chuyển",
    "DELIVERED": "Giao hàng thành công",
    "RETURNED": "Hàng đã trả về",
    "FAILED": "Giao hàng thất bại",
    "CANCELLED": "Đã hủy vận đơn",
}


class ShippingService:
    """Service orchestrating logistics dispatch, tracking, and carrier webhooks."""

    @classmethod
    def dispatch_order(
        cls,
        db: Session,
        order_code: str,
        payload: ShipmentDispatchCreateRequest,
        current_user: User,
    ) -> ShipmentDetailResponse:
        """Create carrier dispatch order for an eligible order (CONFIRMED or PROCESSING)."""
        order = OrderRepository.get_by_code(db, order_code)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng mã '{order_code}'.",
            )

        # Enforce order lifecycle validity
        if order.status in ["PENDING"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đơn hàng đang ở trạng thái chờ xử lý (PENDING). Vui lòng xác nhận đơn trước khi điều vận.",
            )
        if order.status in ["CANCELLED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Đơn hàng đã bị hủy, không thể xuất kho tạo vận đơn.",
            )
        if order.status in ["SHIPPING", "COMPLETED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Đơn hàng đã ở trạng thái '{order.status}', không thể tạo thêm vận đơn mới.",
            )

        # Check for existing shipment (prevent duplicate dispatch)
        existing_shipment = ShipmentRepository.get_by_order_id(db, order.id)
        if existing_shipment and existing_shipment.status != "CANCELLED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Đơn hàng '{order_code}' đã được gắn vận đơn '{existing_shipment.tracking_code}' "
                f"của hãng {existing_shipment.carrier}.",
            )

        # Resolve carrier adapter
        carrier_name = payload.carrier.upper()
        try:
            provider = get_shipping_provider(carrier_name)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        creation_payload = ShipmentCreationPayload(
            order=order,
            weight=payload.weight,
            length=payload.length,
            width=payload.width,
            height=payload.height,
            required_note=payload.required_note,
            staff_notes=payload.staff_notes,
        )

        try:
            res = provider.create_shipment(creation_payload)
        except LiveIntegrationBlockedError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        except ShippingProviderError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

        if not res.success or not res.tracking_code:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Tạo vận đơn thất bại từ cổng {carrier_name}: {res.error_message or 'Lỗi không xác định'}",
            )

        # Save Shipment in MySQL
        shipment = ShipmentRepository.create_shipment(
            db=db,
            order=order,
            carrier=res.carrier,
            tracking_code=res.tracking_code,
            shipping_fee=res.shipping_fee,
            estimated_delivery_date=res.estimated_delivery_date,
        )

        # Append initial tracking checkpoint
        ShipmentRepository.add_event(
            db=db,
            shipment_id=shipment.id,
            status="READY_TO_PICK",
            description=f"Đã tạo vận đơn trên hệ thống {res.carrier}. Sẵn sàng lấy hàng.",
            location="Kho tổng NOVELIA BOOKS",
            raw_payload=res.raw_response,
        )

        # Transition order to SHIPPING
        order.status = "SHIPPING"
        if payload.staff_notes:
            existing_note = order.staff_notes or ""
            order.staff_notes = (
                f"{existing_note}\n[ĐIỀU VẬN] {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')}: "
                f"Đã bàn giao {res.carrier} (Vận đơn: {res.tracking_code})"
            ).strip()

        db.commit()
        db.refresh(shipment)
        db.refresh(order)

        return cls._map_shipment_detail(shipment, order)

    @classmethod
    def get_order_tracking(
        cls, db: Session, order_code: str, current_user: User
    ) -> ShipmentDetailResponse:
        """Retrieve tracking checkpoints. Customer must own the order."""
        order = OrderRepository.get_by_code(db, order_code)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng mã '{order_code}'.",
            )

        # Multi-Tenant Isolation
        user_roles = UserRepository.get_user_role_names(current_user)
        if "ADMIN" not in user_roles and "STAFF" not in user_roles:
            if order.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Bạn không có quyền xem thông tin vận chuyển của đơn hàng này.",
                )

        shipment = ShipmentRepository.get_by_order_id(db, order.id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Đơn hàng '{order_code}' chưa được tạo vận đơn điều vận.",
            )

        return cls._map_shipment_detail(shipment, order)

    @classmethod
    def track_by_tracking_code(
        cls, db: Session, tracking_code: str
    ) -> ShipmentTrackingLookupResponse:
        """Public tracking lookup by carrier tracking code."""
        shipment = ShipmentRepository.get_by_tracking_code(db, tracking_code)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy vận đơn có mã '{tracking_code}'.",
            )

        events = [
            ShipmentEventResponse(
                id=ev.id,
                status=ev.status,
                description=ev.description,
                location=ev.location,
                occurred_at=ev.occurred_at,
            )
            for ev in sorted(shipment.events, key=lambda x: x.occurred_at, reverse=True)
        ]

        order = shipment.order
        return ShipmentTrackingLookupResponse(
            tracking_code=shipment.tracking_code or "",
            order_code=order.order_code if order else "",
            carrier=shipment.carrier,
            status=shipment.status,
            status_label=CARRIER_STATUS_LABELS.get(shipment.status, shipment.status),
            estimated_delivery_date=shipment.estimated_delivery_date,
            delivered_at=shipment.delivered_at,
            events=events,
        )

    @classmethod
    def process_carrier_webhook(
        cls,
        db: Session,
        carrier: str,
        raw_payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> Dict[str, Any]:
        """Verify, authenticate, and synchronize carrier status updates."""
        carrier_name = carrier.upper()
        try:
            provider = get_shipping_provider(carrier_name)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        # Authenticate signature / secret
        if not provider.verify_webhook(raw_payload, headers):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Chữ ký hoặc Secret xác thực webhook {carrier_name} không hợp lệ.",
            )

        event_data = provider.parse_webhook_event(raw_payload, headers)
        if not event_data.tracking_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Thiếu mã vận đơn (tracking_code) trong dữ liệu webhook.",
            )

        shipment = ShipmentRepository.get_by_tracking_code(db, event_data.tracking_code)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy vận đơn '{event_data.tracking_code}' trong hệ thống.",
            )

        # Idempotency and Replay Protection: Check if event already processed
        if ShipmentRepository.has_event_occurred(
            db, shipment.id, event_data.status, event_data.occurred_at
        ):
            return {
                "status": "ignored",
                "message": "Sự kiện webhook trùng lặp đã được ghi nhận trước đó.",
                "tracking_code": event_data.tracking_code,
                "current_shipment_status": shipment.status,
            }

        # Append audit checkpoint
        ShipmentRepository.add_event(
            db=db,
            shipment_id=shipment.id,
            status=event_data.status,
            description=event_data.description,
            location=event_data.location,
            raw_payload=event_data.raw_payload,
            occurred_at=event_data.occurred_at,
        )

        order = shipment.order

        # Synchronize lifecycle status
        if event_data.status in ["READY_TO_PICK", "PICKING", "IN_TRANSIT"]:
            ShipmentRepository.update_shipment_status(db, shipment, event_data.status)
            if order and order.status != "SHIPPING":
                order.status = "SHIPPING"

        elif event_data.status == "DELIVERED":
            delivered_time = event_data.occurred_at or datetime.now(timezone.utc)
            ShipmentRepository.update_shipment_status(
                db, shipment, "DELIVERED", delivered_at=delivered_time
            )
            if order:
                order.status = "COMPLETED"
                # If payment was COD, automatically reconcile to PAID upon delivery confirmation
                if order.payment and order.payment.payment_method == "COD" and order.payment.payment_status != "PAID":
                    order.payment.payment_status = "PAID"
                    order.payment.paid_at = delivered_time

        elif event_data.status in ["RETURNED", "FAILED"]:
            ShipmentRepository.update_shipment_status(db, shipment, event_data.status)
            if order and event_data.status == "RETURNED":
                order.status = "CANCELLED"
                order.cancelled_reason = f"Đơn hàng bị trả lại từ hãng {carrier_name}: {event_data.description}"

        db.commit()
        db.refresh(shipment)
        if order:
            db.refresh(order)

        # Trigger customer notification and audit log for shipping event
        try:
            from app.services.notification_service import NotificationService
            from app.repositories.audit_repo import AuditRepository

            NotificationService.notify_shipping_update(
                db,
                shipment=shipment,
                carrier_status=event_data.status,
                description=event_data.description or f"Trạng thái vận chuyển: {event_data.status}",
            )
            AuditRepository.record_audit(
                db=db,
                action="SHIPMENT_EVENT",
                entity_type="SHIPMENT",
                entity_id=shipment.tracking_code,
                new_values={
                    "carrier": carrier_name,
                    "status": event_data.status,
                    "description": event_data.description,
                    "location": event_data.location,
                    "order_code": order.order_code if order else None,
                },
            )
        except Exception:
            pass

        return {
            "status": "success",
            "tracking_code": event_data.tracking_code,
            "shipment_status": shipment.status,
            "order_status": order.status if order else None,
        }

    @classmethod
    def cancel_shipment(
        cls, db: Session, order_code: str, current_user: User
    ) -> Dict[str, Any]:
        """Staff/Admin cancel shipping dispatch before it is delivered."""
        order = OrderRepository.get_by_code(db, order_code)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy đơn hàng mã '{order_code}'.",
            )

        shipment = ShipmentRepository.get_by_order_id(db, order.id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Đơn hàng '{order_code}' chưa được tạo vận đơn.",
            )

        if shipment.status in ["DELIVERED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vận đơn đã giao thành công, không thể hủy bỏ.",
            )

        provider = get_shipping_provider(shipment.carrier)
        if shipment.tracking_code:
            provider.cancel_shipment(shipment.tracking_code)

        ShipmentRepository.update_shipment_status(db, shipment, "CANCELLED")
        ShipmentRepository.add_event(
            db,
            shipment.id,
            status="CANCELLED",
            description=f"Nhân viên ({current_user.full_name}) đã yêu cầu hủy vận đơn",
            location="Trung tâm điều phối NOVELIA",
        )

        db.commit()
        return {
            "message": f"Đã hủy thành công vận đơn '{shipment.tracking_code}' của hãng {shipment.carrier}.",
            "shipment_id": shipment.id,
            "status": "CANCELLED",
        }

    @classmethod
    def get_providers_status(cls) -> List[ShippingProviderStatusResponse]:
        """Diagnostic check of registered carrier integrations."""
        env = settings.SHIPPING_ENVIRONMENT.lower()

        # GHN Status
        ghn_has_creds = bool(settings.GHN_TOKEN and settings.GHN_SHOP_ID != 0)
        ghn_ready = ghn_has_creds or env != "live"
        ghn_status = ShippingProviderStatusResponse(
            carrier="GHN",
            environment=env,
            is_live_ready=ghn_has_creds,
            status_text="LIVE CONNECTED" if ghn_has_creds else ("SANDBOX READY" if env != "live" else "BLOCKED"),
            api_url=settings.GHN_API_URL,
            notes="Kết nối Giao Hàng Nhanh v2. " + (
                "Đầy đủ credentials." if ghn_has_creds else "Môi trường thử nghiệm / Sandbox."
            ),
        )

        # GHTK Status
        ghtk_has_creds = bool(settings.GHTK_TOKEN)
        ghtk_status = ShippingProviderStatusResponse(
            carrier="GHTK",
            environment=env,
            is_live_ready=ghtk_has_creds,
            status_text="LIVE CONNECTED" if ghtk_has_creds else ("SANDBOX READY" if env != "live" else "BLOCKED"),
            api_url=settings.GHTK_API_URL,
            notes="Kết nối Giao Hàng Tiết Kiệm. " + (
                "Đầy đủ credentials." if ghtk_has_creds else "Môi trường thử nghiệm / Sandbox."
            ),
        )

        # Mock Status
        mock_status = ShippingProviderStatusResponse(
            carrier="MOCK",
            environment="mock",
            is_live_ready=True,
            status_text="OPERATIONAL",
            api_url="local://mock-shipping",
            notes="Bộ giả lập chuyển phát nhanh cho môi trường test và phát triển offline.",
        )

        return [ghn_status, ghtk_status, mock_status]

    @classmethod
    def _map_shipment_detail(cls, shipment: Shipment, order: Order) -> ShipmentDetailResponse:
        events = [
            ShipmentEventResponse(
                id=ev.id,
                status=ev.status,
                description=ev.description,
                location=ev.location,
                occurred_at=ev.occurred_at,
            )
            for ev in sorted(shipment.events, key=lambda x: x.occurred_at, reverse=True)
        ]

        full_address = (
            f"{order.shipping_street_address}, {order.shipping_ward}, "
            f"{order.shipping_district}, {order.shipping_province}"
        )

        return ShipmentDetailResponse(
            id=shipment.id,
            order_id=order.id,
            order_code=order.order_code,
            carrier=shipment.carrier,
            tracking_code=shipment.tracking_code,
            status=shipment.status,
            status_label=CARRIER_STATUS_LABELS.get(shipment.status, shipment.status),
            shipping_fee=Decimal(str(shipment.shipping_fee)),
            estimated_delivery_date=shipment.estimated_delivery_date,
            dispatched_at=shipment.dispatched_at,
            delivered_at=shipment.delivered_at,
            recipient_name=order.recipient_name,
            recipient_phone=order.recipient_phone,
            shipping_address=full_address,
            events=events,
            created_at=shipment.created_at,
        )
