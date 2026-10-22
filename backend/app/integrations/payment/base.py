"""Base abstract payment provider interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from decimal import Decimal

from app.models.commerce import Order
from app.models.payment_shipping import Payment


class PaymentProvider(ABC):
    """Abstract interface defining required contract for payment gateways."""

    @abstractmethod
    def create_payment_intent(
        self, order: Order, payment: Payment, return_url: str = ""
    ) -> Dict[str, Any]:
        """Generate gateway payment intent, redirect URL, or instructions.

        Returns:
            Dict containing 'payment_url', 'instructions', 'transaction_ref', etc.
        """
        pass

    @abstractmethod
    def verify_webhook_signature(
        self, payload: Dict[str, Any], signature: str
    ) -> bool:
        """Verify authenticity of gateway webhook or IPN callback."""
        pass

    @abstractmethod
    def process_callback(
        self, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse raw callback payload into standardized dictionary:

        {
            'order_code': str,
            'amount': Decimal,
            'transaction_id': str,
            'is_success': bool,
            'message': str,
            'raw_data': dict
        }
        """
        pass
