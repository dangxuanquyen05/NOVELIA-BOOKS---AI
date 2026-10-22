"""Mock shipping provider adapter for local testing and offline CI/CD pipelines."""

import hashlib
import hmac
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from app.integrations.shipping.base import (
    ShipmentCreationPayload,
    ShipmentCreationResult,
    ShipmentEventData,
    ShipmentTrackingResult,
    ShippingProvider,
)

MOCK_SHIPPING_SECRET = "novelia-mock-shipping-secret-2026"


def compute_mock_shipping_signature(payload: Dict[str, Any], secret: str = MOCK_SHIPPING_SECRET) -> str:
    """Compute deterministic HMAC-SHA256 signature for mock shipping webhooks."""
    raw_str = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hmac.new(secret.encode("utf-8"), raw_str.encode("utf-8"), hashlib.sha256).hexdigest()


class MockShippingAdapter(ShippingProvider):
    """Deterministic mock shipping carrier simulating GHN/GHTK workflows."""

    def __init__(self, carrier_code: str = "MOCK"):
        self._carrier_code = carrier_code.upper()

    @property
    def carrier_name(self) -> str:
        return self._carrier_code

    def create_shipment(self, payload: ShipmentCreationPayload) -> ShipmentCreationResult:
        order = payload.order
        # Generate predictable mock tracking code
        raw_token = f"{self._carrier_code}_{order.order_code}_{order.id}"
        short_hash = hashlib.md5(raw_token.encode("utf-8")).hexdigest()[:8].upper()
        tracking_code = f"MOCK-{self._carrier_code}-{short_hash}"

        est_date = (datetime.now(timezone.utc) + timedelta(days=3)).date()
        fee = Decimal("30000.00") if order.shipping_fee > 0 else Decimal("0.00")

        return ShipmentCreationResult(
            success=True,
            carrier=self._carrier_code,
            tracking_code=tracking_code,
            shipping_fee=fee,
            estimated_delivery_date=est_date,
            raw_response={
                "code": 200,
                "message": "Success (Mock Adapter)",
                "data": {
                    "order_code": tracking_code,
                    "expected_delivery_time": est_date.isoformat(),
                    "total_fee": float(fee),
                },
            },
        )

    def track_shipment(self, tracking_code: str) -> ShipmentTrackingResult:
        now = datetime.now(timezone.utc)
        return ShipmentTrackingResult(
            tracking_code=tracking_code,
            carrier=self._carrier_code,
            status="IN_TRANSIT",
            status_description="Đang luân chuyển qua bưu cục trung chuyển (MOCK)",
            location="Trung tâm điều vận miền Bắc, Hà Nội",
            occurred_at=now,
            raw_data={"tracking_code": tracking_code, "checkpoint": "IN_TRANSIT_HUB"},
        )

    def cancel_shipment(self, tracking_code: str) -> bool:
        return True

    def verify_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Verify HMAC-SHA256 signature in X-Shipping-Signature or Authorization header."""
        received_sig = (
            headers.get("x-shipping-signature")
            or headers.get("X-Shipping-Signature")
            or headers.get("authorization", "").replace("Bearer ", "")
        )
        if not received_sig:
            return False

        expected_sig = compute_mock_shipping_signature(payload, MOCK_SHIPPING_SECRET)
        return hmac.compare_digest(received_sig, expected_sig)

    def parse_webhook_event(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> ShipmentEventData:
        tracking_code = payload.get("tracking_code") or payload.get("order_code") or ""
        status = payload.get("status", "IN_TRANSIT").upper()
        description = payload.get("description", f"Cập nhật trạng thái {status} từ đơn vị vận chuyển MOCK")
        location = payload.get("location", "Kho phân loại trung tâm")

        occurred_str = payload.get("occurred_at")
        if occurred_str:
            try:
                occurred_at = datetime.fromisoformat(occurred_str)
            except Exception:
                occurred_at = datetime.now(timezone.utc)
        else:
            occurred_at = datetime.now(timezone.utc)

        return ShipmentEventData(
            tracking_code=tracking_code,
            status=status,
            description=description,
            location=location,
            occurred_at=occurred_at,
            raw_payload=payload,
        )
