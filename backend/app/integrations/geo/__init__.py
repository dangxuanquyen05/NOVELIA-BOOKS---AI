"""Geocoding, Reverse Geocoding, and Map integration package for NOVELIA BOOKS."""

from app.integrations.geo.base import (
    GeocodingConfigurationError,
    NormalizedAddress,
    OutOfBoundsError,
    ReverseGeocodingError,
    ReverseGeocodingProvider,
)
from app.integrations.geo.factory import get_reverse_geocoding_provider
from app.integrations.geo.mock import MockReverseGeocodingProvider
from app.integrations.geo.normalization import AddressNormalizationService
from app.integrations.geo.vietmap import VietMapGeocodingProvider

__all__ = [
    "GeocodingConfigurationError",
    "NormalizedAddress",
    "OutOfBoundsError",
    "ReverseGeocodingError",
    "ReverseGeocodingProvider",
    "AddressNormalizationService",
    "VietMapGeocodingProvider",
    "MockReverseGeocodingProvider",
    "get_reverse_geocoding_provider",
]
