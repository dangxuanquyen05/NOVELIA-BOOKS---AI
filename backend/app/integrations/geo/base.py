"""Abstract interfaces and standard data structures for Geocoding and Map providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class ReverseGeocodingError(Exception):
    """Exception raised when reverse geocoding request fails or coordinate lookup returns an error."""
    pass


class GeocodingConfigurationError(ReverseGeocodingError):
    """Raised when an external provider (such as VietMap) is enabled but API credentials are unconfigured."""
    pass


class OutOfBoundsError(ReverseGeocodingError):
    """Raised when coordinates fall outside the supported region (Vietnam territory)."""
    pass


@dataclass
class NormalizedAddress:
    """Standardized representation of a geocoded address normalized for Vietnamese administrative levels."""

    province_name: str
    province_code: str
    district_name: str
    district_code: str
    ward_name: str
    ward_code: str
    street_address: str
    formatted_address: str
    latitude: float
    longitude: float
    place_id: Optional[str] = None
    confidence: float = 0.95
    level: str = "house_number"  # 'house_number', 'street', 'ward', 'district', 'province'
    source_provider: str = "VIETMAP"
    is_mock: bool = False
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert normalized address to dictionary response format."""
        return {
            "province_name": self.province_name,
            "province_code": self.province_code,
            "district_name": self.district_name,
            "district_code": self.district_code,
            "ward_name": self.ward_name,
            "ward_code": self.ward_code,
            "street_address": self.street_address,
            "formatted_address": self.formatted_address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "place_id": self.place_id,
            "confidence": self.confidence,
            "level": self.level,
            "source_provider": self.source_provider,
            "is_mock": self.is_mock,
        }


class ReverseGeocodingProvider(ABC):
    """Abstract contract for reverse geocoding providers (VietMap, Mock, etc.)."""

    @abstractmethod
    async def reverse_geocode(self, lat: float, lng: float) -> NormalizedAddress:
        """Resolve geographical coordinates (lat, lng) to a standardized Vietnamese address."""
        raise NotImplementedError

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if real API credentials and endpoints are validly configured."""
        raise NotImplementedError

    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique identifier string of the provider."""
        raise NotImplementedError
