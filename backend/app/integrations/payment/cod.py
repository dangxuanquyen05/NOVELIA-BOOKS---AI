"""Cash on Delivery (COD) payment provider."""

from typing import Any, Dict
from decimal import Decimal
from app.integrations.payment.base import PaymentProvider
from app.models.commerce import Order
from app.models.payment_shipping import Payment


class CODPaymentProvider(PaymentProvider):
    """Handles Cash on Delivery checkout.

    COD requires no external gateway redirect. Payment status remains PENDING
    until the delivery partner confirms cash collection upon handover.
    """

    def create_payment_intent(
        self, order: Order, payment: Payment, return_url: str = ""
    ) -> Dict[str, Any]:
        return {
            "payment_url": None,
            "instructions": (
                f"Quý khách vui lòng thanh toán số tiền {float(payment.amount):,.0f} VND "
                "bằng tiền mặt trực tiếp cho nhân viên giao hàng khi nhận sách."
            ),
            "gateway": "COD",
            "transaction_ref": payment.payment_code,
            "requires_redirect": False,
        }

    def verify_webhook_signature(
        self, payload: Dict[str, Any], signature: str
    ) -> bool:
        # COD does not have incoming webhook signatures
        return True

    def process_callback(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "order_code": payload.get("order_code", ""),
            "amount": Decimal(str(payload.get("amount", "0"))),
            "transaction_id": payload.get("transaction_id", f"COD-{payload.get('order_code')}"),
            "is_success": True,
            "message": "Thanh toán tiền mặt khi nhận hàng (COD) thành công.",
            "raw_data": payload,
        }
