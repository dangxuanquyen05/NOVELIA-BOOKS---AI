"""Payment provider factory."""

from typing import Dict, Type
from app.integrations.payment.base import PaymentProvider
from app.integrations.payment.cod import CODPaymentProvider
from app.integrations.payment.mock import MockPaymentProvider
from app.integrations.payment.sandbox import VNPaySandboxAdapter

_REGISTRY: Dict[str, PaymentProvider] = {
    "COD": CODPaymentProvider(),
    "MOCK": MockPaymentProvider(),
    "VNPAY": VNPaySandboxAdapter(),
}


def get_payment_provider(payment_method: str) -> PaymentProvider:
    """Retrieve payment provider instance by method key.

    Defaults to MOCK if unknown external gateway, or COD if COD.
    """
    key = payment_method.strip().upper()
    if key in _REGISTRY:
        return _REGISTRY[key]
    if key in ["MOMO", "ZALOPAY", "BANK_TRANSFER"]:
        # Fallback to Mock in dev/test environment
        return _REGISTRY["MOCK"]
    raise ValueError(f"Phương thức thanh toán '{payment_method}' không được hỗ trợ.")
