"""Factory module for instantiating Reverse Geocoding and Map providers."""

import logging
from typing import Optional

from app.core.config import settings
from app.integrations.geo.base import ReverseGeocodingProvider
from app.integrations.geo.mock import MockReverseGeocodingProvider
from app.integrations.geo.vietmap import VietMapGeocodingProvider

logger = logging.getLogger("novelia.geo.factory")


def get_reverse_geocoding_provider(
    provider_name: Optional[str] = None,
) -> ReverseGeocodingProvider:
    """Resolve and instantiate the appropriate geocoding provider based on configuration or explicit override."""
    chosen = (provider_name or settings.GEOCODING_PROVIDER or "auto").lower().strip()

    if chosen == "vietmap":
        return VietMapGeocodingProvider()
    elif chosen == "mock":
        return MockReverseGeocodingProvider(is_fallback=False)
    elif chosen == "auto":
        vietmap_provider = VietMapGeocodingProvider()
        if vietmap_provider.is_configured():
            logger.info("Auto-selected VIETMAP geocoding provider (API key configured).")
            return vietmap_provider
        else:
            logger.info("VIETMAP_API_KEY is not configured; auto-falling back to MockReverseGeocodingProvider with test fixtures.")
            return MockReverseGeocodingProvider(is_fallback=True)
    else:
        logger.warning("Unrecognized GEOCODING_PROVIDER '%s'; falling back to MockReverseGeocodingProvider.", chosen)
        return MockReverseGeocodingProvider(is_fallback=True)
