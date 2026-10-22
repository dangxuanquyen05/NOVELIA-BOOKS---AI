"""Shipping provider integrations module exports."""

from app.integrations.shipping.base import (
    LiveIntegrationBlockedError,
    ShipmentCreationPayload,
    ShipmentCreationResult,
    ShipmentEventData,
    ShipmentTrackingResult,
    ShippingProvider,
    ShippingProviderError,
)
from app.integrations.shipping.factory import get_shipping_provider
from app.integrations.shipping.ghn import GHNShippingAdapter
from app.integrations.shipping.ghtk import GHTKShippingAdapter
from app.integrations.shipping.mock import (
    MOCK_SHIPPING_SECRET,
    MockShippingAdapter,
    compute_mock_shipping_signature,
)

__all__ = [
    "ShippingProvider",
    "ShippingProviderError",
    "LiveIntegrationBlockedError",
    "ShipmentCreationPayload",
    "ShipmentCreationResult",
    "ShipmentTrackingResult",
    "ShipmentEventData",
    "get_shipping_provider",
    "GHNShippingAdapter",
    "GHTKShippingAdapter",
    "MockShippingAdapter",
    "compute_mock_shipping_signature",
    "MOCK_SHIPPING_SECRET",
]
