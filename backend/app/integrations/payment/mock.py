"""Mock payment provider for unit and integration testing."""

import hashlib
import hmac
from decimal import Decimal
from typing import Any, Dict

from app.integrations.payment.base import PaymentProvider
from app.models.commerce import Order
from app.models.payment_shipping import Payment

MOCK_SECRET_KEY = "novelia_books_mock_payment_secret"


def compute_mock_signature(order_code: str, amount: str, secret: str = MOCK_SECRET_KEY) -> str:
    """Compute HMAC-SHA256 signature for mock test verification."""
    data = f"{order_code}|{amount}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()


class MockPaymentProvider(PaymentProvider):
    """Verifiable mock provider for automated tests and sandbox verification."""

    def __init__(self, secret_key: str = MOCK_SECRET_KEY):
        self.secret_key = secret_key

    def create_payment_intent(
        self, order: Order, payment: Payment, return_url: str = ""
    ) -> Dict[str, Any]:
        amount_str = f"{payment.amount:.2f}"
        sig = compute_mock_signature(order.order_code, amount_str, self.secret_key)
        mock_checkout_url = (
            f"http://localhost:8000/mock-gateway/pay?order_code={order.order_code}"
            f"&amount={amount_str}&sig={sig}"
        )
        return {
            "payment_url": mock_checkout_url,
            "instructions": "Vui lòng mở liên kết thử nghiệm thanh toán giả lập.",
            "gateway": "MOCK",
            "transaction_ref": f"MOCK-TX-{payment.payment_code}",
            "requires_redirect": True,
            "signature": sig,
        }

    def verify_webhook_signature(
        self, payload: Dict[str, Any], signature: str
    ) -> bool:
        order_code = payload.get("order_code", "")
        amount = payload.get("amount", "")
        if isinstance(amount, (int, float, Decimal)):
            amount = f"{Decimal(str(amount)):.2f}"
        expected = compute_mock_signature(order_code, str(amount), self.secret_key)
        return hmac.compare_digest(expected, signature)

    def process_callback(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        amount = Decimal(str(payload.get("amount", "0.00")))
        is_success = bool(payload.get("is_success", True))
        return {
            "order_code": payload.get("order_code", ""),
            "amount": amount,
            "transaction_id": payload.get(
                "transaction_id", f"MOCK-GATEWAY-{payload.get('order_code')}"
            ),
            "is_success": is_success,
            "message": "Giao dịch thanh toán cổng Mock thành công." if is_success else "Giao dịch thất bại.",
            "raw_data": payload,
        }
