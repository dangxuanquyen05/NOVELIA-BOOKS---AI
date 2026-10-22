"""Base abstract shipping provider interface and standard data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.commerce import Order


class ShippingProviderError(Exception):
    """Exception raised when carrier integration fails or credentials are blocked."""
    pass


class LiveIntegrationBlockedError(ShippingProviderError):
    """Explicitly raised when LIVE carrier integration is attempted without verifiable merchant credentials."""
    pass


@dataclass
class ShipmentCreationPayload:
    """Standardized order dispatch payload passed to shipping adapters."""

    order: Order
    weight: int = 500  # Grams
    length: int = 20   # cm
    width: int = 15    # cm
    height: int = 5    # cm
    required_note: str = "CHOXEMHANGKHONGTHU"  # GHN note code
    staff_notes: Optional[str] = None


@dataclass
class ShipmentCreationResult:
    """Standardized result returned after carrier order creation."""

    success: bool
    carrier: str
    tracking_code: str
    shipping_fee: Decimal = Decimal("0.00")
    estimated_delivery_date: Optional[date] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class ShipmentTrackingResult:
    """Standardized result returned after querying carrier tracking."""

    tracking_code: str
    carrier: str
    status: str  # PENDING, READY_TO_PICK, PICKING, IN_TRANSIT, DELIVERED, RETURNED, FAILED, CANCELLED
    status_description: str
    location: Optional[str] = None
    occurred_at: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShipmentEventData:
    """Parsed webhook event checkpoint."""

    tracking_code: str
    status: str
    description: str
    location: Optional[str] = None
    occurred_at: Optional[datetime] = None
    raw_payload: Dict[str, Any] = field(default_factory=dict)


class ShippingProvider(ABC):
    """Abstract interface defining the strict contract for all shipping carriers."""

    @property
    @abstractmethod
    def carrier_name(self) -> str:
        """Name of the logistics carrier (e.g., 'GHN', 'GHTK', 'MOCK')."""
        pass

    @abstractmethod
    def create_shipment(self, payload: ShipmentCreationPayload) -> ShipmentCreationResult:
        """Create carrier dispatch order and generate formal tracking code."""
        pass

    @abstractmethod
    def track_shipment(self, tracking_code: str) -> ShipmentTrackingResult:
        """Query real-time shipping checkpoints from carrier."""
        pass

    @abstractmethod
    def cancel_shipment(self, tracking_code: str) -> bool:
        """Request carrier to cancel dispatch if not yet in transit."""
        pass

    @abstractmethod
    def verify_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """Authenticate carrier webhook signature or token."""
        pass

    @abstractmethod
    def parse_webhook_event(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> ShipmentEventData:
        """Parse raw carrier webhook into normalized shipment event data."""
        pass
