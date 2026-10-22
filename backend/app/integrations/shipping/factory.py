"""Shipping provider factory resolving carrier instances."""

from typing import Dict
from app.core.config import settings
from app.integrations.shipping.base import ShippingProvider
from app.integrations.shipping.ghn import GHNShippingAdapter
from app.integrations.shipping.ghtk import GHTKShippingAdapter
from app.integrations.shipping.mock import MockShippingAdapter


def get_shipping_provider(carrier: str = "") -> ShippingProvider:
    """Retrieve shipping provider instance by carrier identifier (GHN, GHTK, MOCK).
    
    If carrier is empty, uses DEFAULT_SHIPPING_CARRIER from settings.
    If SHIPPING_ENVIRONMENT is 'mock', returns MockShippingAdapter.
    """
    selected_carrier = (carrier or settings.DEFAULT_SHIPPING_CARRIER).strip().upper()
    env = settings.SHIPPING_ENVIRONMENT.lower()

    if env == "mock":
        return MockShippingAdapter(carrier_code=selected_carrier)

    if selected_carrier == "GHN":
        return GHNShippingAdapter()
    elif selected_carrier == "GHTK":
        return GHTKShippingAdapter()
    elif selected_carrier == "MOCK":
        return MockShippingAdapter(carrier_code="MOCK")

    raise ValueError(f"Nhà vận chuyển '{carrier}' không được hỗ trợ trong hệ thống.")
