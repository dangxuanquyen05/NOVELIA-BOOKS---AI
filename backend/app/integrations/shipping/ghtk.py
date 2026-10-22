"""Giao Hàng Tiết Kiệm (GHTK) API Integration Adapter."""

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

GHTK_STATUS_MAPPING = {
    -1: "CANCELLED",
    1: "READY_TO_PICK",
    2: "PICKING",
    3: "IN_TRANSIT",
    4: "IN_TRANSIT",
    12: "IN_TRANSIT",
    5: "DELIVERED",
    6: "DELIVERED",
    7: "FAILED",
    9: "FAILED",
    10: "FAILED",
    11: "RETURNED",
    20: "RETURNED",
    21: "RETURNED",
}


class GHTKShippingAdapter(ShippingProvider):
    """Adapter connecting to Giao Hàng Tiết Kiệm (GHTK) APIs."""

    def __init__(self):
        self.api_url = settings.GHTK_API_URL.rstrip("/")
        self.token = settings.GHTK_TOKEN.strip()
        self.env = settings.SHIPPING_ENVIRONMENT.lower()

    @property
    def carrier_name(self) -> str:
        return "GHTK"

    def _check_live_credentials(self):
        if self.env == "live" and not self.token:
            raise LiveIntegrationBlockedError(
                "GHTK Live Integration is BLOCKED: Thiếu GHTK_TOKEN xác thực đối tác doanh nghiệp "
                "trong môi trường sản xuất. Vui lòng cấu hình .env hoặc chuyển sang chế độ sandbox/mock."
            )

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Token": self.token,
        }

    def create_shipment(self, payload: ShipmentCreationPayload) -> ShipmentCreationResult:
        self._check_live_credentials()

        order = payload.order
        is_cod = order.payment and order.payment.payment_method == "COD" and order.payment.payment_status != "PAID"
        cod_amount = int(order.total_amount) if is_cod else 0

        # Construct products
        products = []
        for it in order.items:
            products.append({
                "name": it.title_snapshot[:80],
                "weight": float(payload.weight) / 1000.0,  # kg
                "quantity": it.quantity,
                "product_code": it.sku_snapshot or f"SKU-{it.book_id}",
            })

        order_data = {
            "id": order.order_code,
            "pick_name": "NOVELIA BOOKS Kho Tổng",
            "pick_address": "Số 10 Phạm Văn Đồng",
            "pick_province": "Hà Nội",
            "pick_district": "Cầu Giấy",
            "pick_tel": "0987654321",
            "tel": order.recipient_phone,
            "name": order.recipient_name,
            "address": order.shipping_street_address,
            "province": order.shipping_province,
            "district": order.shipping_district,
            "is_freeship": 1,
            "pick_money": cod_amount,
            "note": payload.staff_notes or f"Đơn hàng NOVELIA #{order.order_code}",
            "value": int(order.total_amount),
        }

        # Sandbox fallback if no token
        if not self.token:
            tracking_code = f"GHTK-DEV-{order.order_code}"
            return ShipmentCreationResult(
                success=True,
                carrier="GHTK",
                tracking_code=tracking_code,
                shipping_fee=Decimal("30000.00"),
                estimated_delivery_date=None,
                raw_response={
                    "success": True,
                    "message": "GHTK Sandbox Mock (Token not configured)",
                    "order": {"label": tracking_code, "fee": "30000"},
                },
            )

        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    f"{self.api_url}/order",
                    headers=self._get_headers(),
                    json={"products": products, "order": order_data},
                )
                data = res.json()
                if res.status_code == 200 and data.get("success"):
                    resp_order = data.get("order", {})
                    tracking_code = resp_order.get("label") or ""
                    fee = Decimal(str(resp_order.get("fee", 0)))
                    return ShipmentCreationResult(
                        success=True,
                        carrier="GHTK",
                        tracking_code=tracking_code,
                        shipping_fee=fee,
                        raw_response=data,
                    )
                else:
                    return ShipmentCreationResult(
                        success=False,
                        carrier="GHTK",
                        tracking_code="",
                        error_message=data.get("message") or f"Lỗi GHTK HTTP {res.status_code}",
                        raw_response=data,
                    )
        except httpx.TimeoutException:
            raise ShippingProviderError("Kết nối tới máy chủ GHTK bị quá thời gian chờ (Timeout 15s).")
        except Exception as e:
            raise ShippingProviderError(f"Lỗi gửi yêu cầu tới cổng GHTK: {str(e)}")

    def track_shipment(self, tracking_code: str) -> ShipmentTrackingResult:
        self._check_live_credentials()

        if not self.token:
            return ShipmentTrackingResult(
                tracking_code=tracking_code,
                carrier="GHTK",
                status="IN_TRANSIT",
                status_description="Đang luân chuyển trên mạng lưới GHTK Sandbox",
                location="Kho phân loại GHTK",
                occurred_at=datetime.now(timezone.utc),
                raw_data={"tracking_code": tracking_code, "note": "GHTK Sandbox simulation"},
            )

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    f"{self.api_url}/v2/cache/{tracking_code}",
                    headers=self._get_headers(),
                )
                data = res.json()
                if res.status_code == 200 and data.get("success"):
                    order_info = data.get("order", {})
                    status_id = int(order_info.get("status", 1))
                    norm_status = GHTK_STATUS_MAPPING.get(status_id, "IN_TRANSIT")
                    return ShipmentTrackingResult(
                        tracking_code=tracking_code,
                        carrier="GHTK",
                        status=norm_status,
                        status_description=order_info.get("status_text") or f"Trạng thái {status_id}",
                        location=order_info.get("current_warehouse"),
                        occurred_at=datetime.now(timezone.utc),
                        raw_data=order_info,
                    )
                else:
                    return ShipmentTrackingResult(
                        tracking_code=tracking_code,
                        carrier="GHTK",
                        status="PENDING",
                        status_description=data.get("message") or "Không tìm thấy dữ liệu vận đơn GHTK",
                        raw_data=data,
                    )
        except Exception as e:
            raise ShippingProviderError(f"Không thể tra cứu vận đơn GHTK: {str(e)}")

    def cancel_shipment(self, tracking_code: str) -> bool:
        self._check_live_credentials()
        if not self.token:
            return True

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"{self.api_url}/cancel/{tracking_code}",
                    headers=self._get_headers(),
                )
                data = res.json()
                return bool(res.status_code == 200 and data.get("success"))
        except Exception:
            return False

    def verify_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Verify GHTK Webhook secret token."""
        secret = (
            headers.get("x-ghtk-secret")
            or headers.get("X-GHTK-Secret")
            or headers.get("authorization", "").replace("Bearer ", "")
        )
        if not secret:
            return False
        return secret == settings.GHTK_WEBHOOK_SECRET

    def parse_webhook_event(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> ShipmentEventData:
        tracking_code = payload.get("label_id") or payload.get("partner_id") or ""
        status_id = payload.get("status_id")
        try:
            status_num = int(status_id) if status_id is not None else 3
        except Exception:
            status_num = 3

        norm_status = GHTK_STATUS_MAPPING.get(status_num, "IN_TRANSIT")
        desc = payload.get("reason") or f"GHTK cập nhật trạng thái (Mã: {status_num})"
        loc = payload.get("location")

        action_time_str = payload.get("action_time")
        if action_time_str:
            try:
                occurred_at = datetime.fromisoformat(str(action_time_str).replace("Z", "+00:00"))
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
