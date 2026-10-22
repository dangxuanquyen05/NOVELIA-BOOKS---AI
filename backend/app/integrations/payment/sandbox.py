"""VNPay sandbox payment provider adapter."""

import hashlib
import hmac
import urllib.parse
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict

from app.integrations.payment.base import PaymentProvider
from app.models.commerce import Order
from app.models.payment_shipping import Payment


class VNPaySandboxAdapter(PaymentProvider):
    """VNPay Sandbox Gateway implementation with HMAC-SHA512 verification."""

    SANDBOX_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"

    def __init__(
        self,
        tmn_code: str = "NOVELIADEMO",
        hash_secret: str = "NOVELIAVNSECRET2026",
    ):
        self.tmn_code = tmn_code
        self.hash_secret = hash_secret

    def _generate_hmac_sha512(self, data_str: str) -> str:
        return hmac.new(
            self.hash_secret.encode("utf-8"),
            data_str.encode("utf-8"),
            hashlib.sha512,
        ).hexdigest()

    def create_payment_intent(
        self, order: Order, payment: Payment, return_url: str = "http://localhost:5173/payment/vnpay-return"
    ) -> Dict[str, Any]:
        """Generate VNPay checkout URL with cryptographic SHA512 signature."""
        amount_vnp = int(payment.amount * 100)  # VNPay uses integer amount * 100
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

        params = {
            "vnp_Version": "2.1.0",
            "vnp_Command": "pay",
            "vnp_TmnCode": self.tmn_code,
            "vnp_Amount": str(amount_vnp),
            "vnp_CurrCode": "VND",
            "vnp_TxnRef": order.order_code,
            "vnp_OrderInfo": f"Thanh toan don hang {order.order_code} tai Novelia Books",
            "vnp_OrderType": "billpayment",
            "vnp_Locale": "vn",
            "vnp_ReturnUrl": return_url,
            "vnp_IpAddr": "127.0.0.1",
            "vnp_CreateDate": now_str,
        }

        # VNPay requires sorted parameter string
        sorted_keys = sorted(params.keys())
        query_parts = []
        for k in sorted_keys:
            query_parts.append(f"{k}={urllib.parse.quote_plus(str(params[k]))}")

        hash_data = "&".join(query_parts)
        secure_hash = self._generate_hmac_sha512(hash_data)
        payment_url = f"{self.SANDBOX_URL}?{hash_data}&vnp_SecureHash={secure_hash}"

        return {
            "payment_url": payment_url,
            "instructions": "Vui lòng mở liên kết cổng thanh toán VNPay Sandbox để thanh toán an toàn.",
            "gateway": "VNPAY",
            "transaction_ref": order.order_code,
            "requires_redirect": True,
            "secure_hash": secure_hash,
        }

    def verify_webhook_signature(
        self, payload: Dict[str, Any], signature: str
    ) -> bool:
        """Verify checksum from VNPay IPN callback."""
        clean_params = {}
        for k, v in payload.items():
            if k not in ["vnp_SecureHash", "vnp_SecureHashType", "signature"]:
                clean_params[k] = str(v)

        sorted_keys = sorted(clean_params.keys())
        query_parts = []
        for k in sorted_keys:
            query_parts.append(f"{k}={urllib.parse.quote_plus(clean_params[k])}")

        hash_data = "&".join(query_parts)
        expected_hash = self._generate_hmac_sha512(hash_data)
        return hmac.compare_digest(expected_hash.lower(), signature.lower())

    def process_callback(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        response_code = payload.get("vnp_ResponseCode", "")
        is_success = response_code == "00"
        amount_raw = payload.get("vnp_Amount", "0")
        try:
            amount = Decimal(str(int(amount_raw) / 100))
        except (ValueError, TypeError):
            amount = Decimal("0.00")

        return {
            "order_code": payload.get("vnp_TxnRef", ""),
            "amount": amount,
            "transaction_id": payload.get(
                "vnp_TransactionNo", f"VNPAY-{payload.get('vnp_TxnRef')}"
            ),
            "is_success": is_success,
            "message": "Giao dịch VNPay thành công." if is_success else f"Giao dịch VNPay thất bại (Mã lỗi: {response_code})",
            "raw_data": payload,
        }
