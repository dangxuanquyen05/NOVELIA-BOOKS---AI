"""Giao Hàng Nhanh (GHN) API v2 Integration Adapter."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings
from app.integrations.shipping.base import (
    LiveIntegrationBlockedError,
    ShipmentCreationPayload,
    ShipmentCreationResult,
    ShipmentEventData,
    ShipmentTrackingResult,
    ShippingProvider,
    ShippingProviderError,
)

GHN_STATUS_MAPPING = {
    "ready_to_pick": "READY_TO_PICK",
    "picking": "PICKING",
    "cancel": "CANCELLED",
    "money_collect_picking": "PICKING",
    "picked": "IN_TRANSIT",
    "storing": "IN_TRANSIT",
    "transporting": "IN_TRANSIT",
    "sorting": "IN_TRANSIT",
    "delivering": "IN_TRANSIT",
    "money_collect_delivering": "IN_TRANSIT",
    "delivered": "DELIVERED",
    "delivery_fail": "FAILED",
    "waiting_to_return": "RETURNED",
    "return": "RETURNED",
    "return_transporting": "RETURNED",
    "return_sorting": "RETURNED",
    "returning": "RETURNED",
    "return_fail": "FAILED",
    "returned": "RETURNED",
    "damage": "FAILED",
    "lost": "FAILED",
}


class GHNShippingAdapter(ShippingProvider):
    """Adapter connecting to Giao Hàng Nhanh Open API v2."""

    def __init__(self):
        self.api_url = settings.GHN_API_URL.rstrip("/")
        self.token = settings.GHN_TOKEN.strip()
        self.shop_id = settings.GHN_SHOP_ID
        self.env = settings.SHIPPING_ENVIRONMENT.lower()

    @property
    def carrier_name(self) -> str:
        return "GHN"

    def _check_live_credentials(self):
        """Enforce non-negotiable rule: LIVE integration is BLOCKED without verified credentials."""
        if self.env == "live" and (not self.token or self.shop_id == 0):
            raise LiveIntegrationBlockedError(
                "GHN Live Integration is BLOCKED: Thiếu thông tin xác thực doanh nghiệp "
                "(GHN_TOKEN hoặc GHN_SHOP_ID chưa được cấp trong môi trường sản xuất)."
            )

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Token": self.token,
            "ShopId": str(self.shop_id),
        }

    def create_shipment(self, payload: ShipmentCreationPayload) -> ShipmentCreationResult:
        self._check_live_credentials()

        order = payload.order
        is_cod = order.payment and order.payment.payment_method == "COD" and order.payment.payment_status != "PAID"
        cod_amount = int(order.total_amount) if is_cod else 0

        # Construct GHN items array
        items = []
        for it in order.items:
            items.append({
                "name": it.title_snapshot[:80],
                "code": it.sku_snapshot or f"SKU-{it.book_id}",
                "quantity": it.quantity,
                "price": int(it.price_at_purchase),
            })

        # Official GHN v2 request body
        body = {
            "payment_type_id": 1,  # Shop pays shipping
            "note": payload.staff_notes or f"Đơn hàng NOVELIA #{order.order_code}",
            "required_note": payload.required_note or "CHOXEMHANGKHONGTHU",
            "client_order_code": order.order_code,
            "to_name": order.recipient_name,
            "to_phone": order.recipient_phone,
            "to_address": order.shipping_street_address,
            "to_ward_name": order.shipping_ward,
            "to_district_name": order.shipping_district,
            "to_province_name": order.shipping_province,
            "cod_amount": cod_amount,
            "weight": payload.weight,
            "length": payload.length,
            "width": payload.width,
            "height": payload.height,
            "service_type_id": 2,  # Chuẩn chuyển phát thương mại điện tử
            "items": items,
        }

        # If token is empty in sandbox/dev mode, simulate response without failing network
        if not self.token:
            # Deterministic sandbox mock
            tracking_code = f"GHN-DEV-{order.order_code}"
            return ShipmentCreationResult(
                success=True,
                carrier="GHN",
                tracking_code=tracking_code,
                shipping_fee=Decimal("30000.00"),
                estimated_delivery_date=None,
                raw_response={
                    "code": 200,
                    "message": "Success (GHN Sandbox Mock - Token not configured)",
                    "data": {"order_code": tracking_code, "total_fee": 30000},
                },
            )

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    f"{self.api_url}/shipping-order/create",
                    headers=self._get_headers(),
                    json=body,
                )
                data = res.json()
                if res.status_code == 200 and data.get("code") == 200:
                    ghn_data = data.get("data", {})
                    tracking_code = ghn_data.get("order_code") or ""
                    fee = Decimal(str(ghn_data.get("total_fee", 0)))
                    est_str = ghn_data.get("expected_delivery_time")
                    est_date = None
                    if est_str:
                        try:
                            est_date = datetime.fromisoformat(est_str.replace("Z", "+00:00")).date()
                        except Exception:
                            pass

                    return ShipmentCreationResult(
                        success=True,
                        carrier="GHN",
                        tracking_code=tracking_code,
                        shipping_fee=fee,
                        estimated_delivery_date=est_date,
                        raw_response=data,
                    )
                else:
                    err_msg = data.get("message_display") or data.get("message") or f"Lỗi GHN HTTP {res.status_code}"
                    return ShipmentCreationResult(
                        success=False,
                        carrier="GHN",
                        tracking_code="",
                        error_message=err_msg,
                        raw_response=data,
                    )
        except httpx.TimeoutException:
            raise ShippingProviderError("Kết nối tới máy chủ GHN bị quá thời gian chờ (Timeout 15s).")
        except Exception as e:
            raise ShippingProviderError(f"Lỗi gửi yêu cầu tới cổng GHN: {str(e)}")

    def track_shipment(self, tracking_code: str) -> ShipmentTrackingResult:
        self._check_live_credentials()

        if not self.token:
            return ShipmentTrackingResult(
                tracking_code=tracking_code,
                carrier="GHN",
                status="IN_TRANSIT",
                status_description="Đang luân chuyển trên mạng lưới GHN Sandbox",
                location="Bưu cục phân loại GHN",
                occurred_at=datetime.now(timezone.utc),
                raw_data={"tracking_code": tracking_code, "note": "GHN Sandbox simulation"},
            )

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"{self.api_url}/shipping-order/detail",
                    headers=self._get_headers(),
                    json={"order_code": tracking_code},
                )
                data = res.json()
                if res.status_code == 200 and data.get("code") == 200:
                    order_info = data.get("data", {})
                    raw_status = (order_info.get("status") or "").lower()
                    norm_status = GHN_STATUS_MAPPING.get(raw_status, "IN_TRANSIT")
                    return ShipmentTrackingResult(
                        tracking_code=tracking_code,
                        carrier="GHN",
                        status=norm_status,
                        status_description=order_info.get("status_name") or f"Trạng thái {raw_status}",
                        location=order_info.get("current_warehouse"),
                        occurred_at=datetime.now(timezone.utc),
                        raw_data=order_info,
                    )
                else:
                    return ShipmentTrackingResult(
                        tracking_code=tracking_code,
                        carrier="GHN",
                        status="PENDING",
                        status_description=data.get("message") or "Không tìm thấy dữ liệu vận đơn GHN",
                        raw_data=data,
                    )
        except Exception as e:
            raise ShippingProviderError(f"Không thể tra cứu trạng thái vận đơn GHN: {str(e)}")

    def cancel_shipment(self, tracking_code: str) -> bool:
        self._check_live_credentials()
        if not self.token:
            return True

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"{self.api_url}/shipping-order/cancel",
                    headers=self._get_headers(),
                    json={"order_codes": [tracking_code]},
                )
                data = res.json()
                return bool(res.status_code == 200 and data.get("code") == 200)
        except Exception:
            return False

    def verify_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Verify GHN Webhook secret token."""
        secret = (
            headers.get("x-ghn-secret")
            or headers.get("X-GHN-Secret")
            or headers.get("authorization", "").replace("Bearer ", "")
        )
        if not secret:
            return False
        return secret == settings.GHN_WEBHOOK_SECRET

    def parse_webhook_event(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> ShipmentEventData:
        tracking_code = payload.get("OrderCode") or payload.get("order_code") or ""
        raw_status = (payload.get("Status") or payload.get("status") or "").lower()
        norm_status = GHN_STATUS_MAPPING.get(raw_status, "IN_TRANSIT")
        desc = payload.get("Description") or f"GHN cập nhật trạng thái: {raw_status.upper()}"
        loc = payload.get("Warehouse") or payload.get("location")

        time_val = payload.get("Time")
        if time_val:
            try:
                occurred_at = datetime.fromisoformat(str(time_val).replace("Z", "+00:00"))
            except Exception:
                occurred_at = datetime.now(timezone.utc)
        else:
            occurred_at = datetime.now(timezone.utc)

        return ShipmentEventData(
            tracking_code=tracking_code,
            status=norm_status,
            description=desc,
            location=loc,
            occurred_at=occurred_at,
            raw_payload=payload,
        )
